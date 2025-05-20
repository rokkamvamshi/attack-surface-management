import subprocess
import os
import json
import secrets
import string
from datetime import datetime, timedelta
import socket
from concurrent.futures import ThreadPoolExecutor
import requests
from urllib3.exceptions import InsecureRequestWarning

# Suppress insecure request warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.utils import timezone
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .reports import report_builder, generate_report, report_data_api
from .debug_utils import log_request, log_data, log_exception
import json
import traceback
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# Import your debug utils
from .debug_utils import log_request, log_data, log_exception


class ExtendedJSONEncoder(DjangoJSONEncoder):
    """Extended JSON encoder that handles additional types"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)
        
def json_response(data, status=200):
    """Create a JSON response with proper encoding"""
    return JsonResponse(
        data,
        encoder=ExtendedJSONEncoder,
        safe=False,
        status=status
    )

# Import models
from .models import (
    User, ScanResult, NucleiResult, UserProfile, 
    UserActivity, ApiKey, UserFeedback
)

# Constants and configurations
SUBFINDER_PATH = "subdominator"
NUCLEI_PATH = "nuclei"
NUCLEI_TEMPLATES_PATH = settings.NUCLEI_TEMPLATES_PATH
TMP_RESULTS_PATH = settings.TMP_RESULTS_PATH
BASE_RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scan_results")

# Bug class templates mapping
BUG_CLASS_TEMPLATES = {
    "xss": "xss",
    "sqli": "sqli",
    "misconfig": "misconfiguration",
    "rce": "rce",
    "default-login": "default-logins",
    "exposed-panels": "exposed-panels",
    "exposures": "exposures",
    "takeovers": "takeovers",
    "technologies": "technologies",
    "token-spray": "token-spray",
    "osint": "osint",
    "cves": "cves",
}

# Helper Functions
def run_command(command):
    """Run a shell command and return the output safely"""
    try:
        result = subprocess.run(
            command, 
            check=True, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}\nError: {e.stderr}")
        return None

def create_results_folder(domain):
    """Create a folder for storing scan results"""
    folder_path = os.path.join(BASE_RESULTS_DIR, f"{domain}_results")
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def is_subdomain_live(subdomain, timeout=3):
    """Check if a subdomain is responsive"""
    try:
        # Try HTTPS first
        url = f"https://{subdomain}"
        response = requests.head(url, timeout=timeout, verify=False, allow_redirects=True)
        if response.status_code < 500:  # Accept any non-server error response
            return True
    except requests.exceptions.RequestException:
        # If HTTPS fails, try HTTP
        try:
            url = f"http://{subdomain}"
            response = requests.head(url, timeout=timeout, verify=False, allow_redirects=True)
            if response.status_code < 500:
                return True
        except requests.exceptions.RequestException:
            # If HTTP request fails, try a basic socket connection to port 80
            try:
                socket.create_connection((subdomain, 80), timeout=timeout)
                return True
            except (socket.timeout, socket.error):
                return False
    return False

def filter_live_subdomains(subdomains, max_workers=10):
    """Filter a list of subdomains to only include those that are live"""
    live_subdomains = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a dictionary mapping subdomain to its future result
        future_to_subdomain = {
            executor.submit(is_subdomain_live, subdomain): subdomain 
            for subdomain in subdomains
        }
        
        # Process the results as they complete
        for future in future_to_subdomain:
            subdomain = future_to_subdomain[future]
            try:
                if future.result():
                    live_subdomains.append(subdomain)
            except Exception:
                # If there's an error checking the subdomain, consider it dead
                pass
    
    return live_subdomains

def run_subfinder(target, folder_path):
    """Run subfinder tool to discover subdomains"""
    output_file = os.path.join(folder_path, "subdomains_subfinder.txt")
    result = run_command(f"{SUBFINDER_PATH} -d {target} --silent -o {output_file}")
    
    # Read the subdomains from the output file
    subdomains = []
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            subdomains = [line.strip() for line in f if line.strip()]
    
    # Keep original list as backup
    original_subdomains = subdomains.copy()
    
    # Filter to keep only live subdomains
    if subdomains:
        print(f"Found {len(subdomains)} potential subdomains. Validating...")
        live_subdomains = filter_live_subdomains(subdomains)
        print(f"Validated {len(live_subdomains)} live subdomains out of {len(subdomains)}")
        
        # If we found some live subdomains, use those
        if live_subdomains:
            with open(output_file, 'w') as f:
                for subdomain in live_subdomains:
                    f.write(f"{subdomain}\n")
            return '\n'.join(live_subdomains)
        else:
            # If no live subdomains found, fall back to original list
            print("No live subdomains found, using original subdomain list")
            return '\n'.join(original_subdomains)
    
    return ""

def record_user_activity(user, activity_type, description):
    """Helper function to record user activity"""
    try:
        UserActivity.objects.create(
            user=user,
            activity_type=activity_type,
            description=description
        )
    except Exception as e:
        print(f"Failed to record user activity: {e}")


# Authentication Views
def signup_view(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Check if a profile already exists before creating a new one
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'completed_onboarding': False}
            )
            
            # Create activity record
            record_user_activity(
                user=user,
                activity_type='login',
                description='Account created'
            )
            
            messages.success(request, "Account created successfully! Please log in.")
            return redirect('login')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, "Both username and password are required.")
            return render(request, 'login.html')
            
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Create activity record
            record_user_activity(
                user=user,
                activity_type='login',
                description='Logged in'
            )
            
            # Check if user needs to complete onboarding
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'completed_onboarding': False}
            )
            if not profile.completed_onboarding:
                return redirect('onboarding')
                
            return redirect('protected_view')  # Main dashboard/home
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'login.html')

def logout_view(request):
    """Handle user logout"""
    if request.user.is_authenticated:
        # Create activity record
        record_user_activity(
            user=request.user,
            activity_type='login',
            description='Logged out'
        )
    logout(request)  # Log the user out
    return redirect('landing')


# Landing Page Views
def landing(request):
    """Display the landing page"""
    if request.user.is_authenticated:
        return redirect('protected_view')  # Redirect to the main view if already logged in
    return render(request, 'landing-page.html')

def about_us(request):
    """Display the about us page"""
    return render(request, 'about.html')

# Main Scanning Views
@login_required
def view(request):
    """Main view for domain scanning"""
    if request.method == 'POST':
        target = request.POST.get('domain')
        if not target:
            return JsonResponse({"error": "Domain is required"}, status=400)

        try:
            folder_path = create_results_folder(target)
            results = {}

            # Run subfinder and get filtered subdomains
            subfinder_results = run_subfinder(target, folder_path)
            
            if subfinder_results is None:
                return JsonResponse({"error": "Failed to run subfinder"}, status=500)

            # Convert to list if it's not None
            subfinder_list = subfinder_results.strip().split('\n') if subfinder_results.strip() else []
            results['subfinder'] = subfinder_list
            results['domain'] = target
            
            # Save results in the database
            try:
                scan_result = ScanResult.objects.create(
                    user=request.user,
                    target=target,
                    subdomains='\n'.join(results['subfinder'])
                )
                
                # Create activity record
                record_user_activity(
                    user=request.user,
                    activity_type='scan',
                    description=f'Scanned domain: {target}'
                )
                
                print(f"Successfully created scan result with ID: {scan_result.id}")
            except Exception as e:
                print(f"Error creating scan result: {str(e)}")
                # Continue without saving to database
            
            return render(request, 'index.html', {"results": results})
        except Exception as e:
            print(f"Error during scan: {str(e)}")
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
    
    return render(request, 'index.html')

@login_required
def scan_page(request):
    """Display the scan page with domains and subdomains"""
    # Fetch distinct domains for the dropdown
    domains = ScanResult.objects.filter(user=request.user).values_list('target', flat=True).distinct()
    subdomains = ScanResult.objects.filter(user=request.user).values_list('subdomains', flat=True).distinct()
    subdomains = '\n'.join(subdomains).split('\n')
    subdomains = list(set(filter(None, subdomains)))  # Filter empty strings
    
    return render(request, 'scan.html', {
        'domainresults': {
            'domains': domains,
            'subdomains': subdomains
        }
    })

@login_required
def scans_page(request):
    """Display the scan page with domains"""
    domains = ScanResult.objects.filter(user=request.user).values_list('target', flat=True).distinct()
    return render(request, 'scan.html', {'domains': domains})

@login_required
def get_subdomain(request, domain):
    """Get subdomains for a specific domain"""
    # Fetch subdomains associated with the selected domain for the current user
    subdomains = ScanResult.objects.filter(user=request.user, target=domain).values_list('subdomains', flat=True)
    subdomains = '\n'.join(subdomains).split('\n')  # Split subdomains by newline
    subdomains = list(set(filter(None, subdomains)))  # Remove duplicates and empty strings
    return JsonResponse({'subdomains': subdomains})

@csrf_exempt
@login_required
def save_scan(request):
    """Handle AJAX requests to save vulnerability scan results"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            domain = data.get('domain')
            subdomain = data.get('subdomain')
            bug_class = data.get('bug_class', "misconfig")  # Default to Misconfig

            if not domain or not subdomain or not bug_class:
                return JsonResponse({"status": "error", "message": "Missing fields"}, status=400)

            print(f"Received scan request: {data}")

            # Define scan output path
            output_path = os.path.join(TMP_RESULTS_PATH, f"{subdomain}.json")

            # Determine Nuclei template path based on bug class selection
            if bug_class.lower() == "all":
                template_path = NUCLEI_TEMPLATES_PATH  # Scan all templates
            else:
                template_dir = BUG_CLASS_TEMPLATES.get(bug_class.lower())
                if not template_dir:
                    return JsonResponse({"status": "error", "message": "Invalid bug class"}, status=400)

                template_path = os.path.join(NUCLEI_TEMPLATES_PATH, template_dir)

                # Ensure the template directory exists
                if not os.path.exists(template_path):
                    return JsonResponse({"status": "error", "message": f"Template path not found: {template_path}"}, status=400)

            # Run Nuclei scan with JSON output
            cmd = [
                NUCLEI_PATH, "-t", template_path,
                "-u", subdomain, "-j", "-silent"
            ]

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                return JsonResponse({"error": f"Nuclei scan failed: {error_msg}"}, status=500)

            # Parse JSON line by line
            results_list = []
            for line in stdout.decode().splitlines():
                if not line.strip():
                    continue
                    
                try:
                    result = json.loads(line.strip())
                    results_list.append({
                        "template_id": result.get("template-id"),
                        "template_name": result["info"].get("name", "Unknown Vulnerability"),
                        "severity": result["info"].get("severity", "info"),
                        "tags": ",".join(result["info"].get("tags", [])),
                        "url": result.get("url", ""),
                        "ip_address": result.get("ip", ""),
                        "protocol": result.get("type", "http"),
                        "timestamp": result.get("timestamp", datetime.now().isoformat()),
                        "curl_command": result.get("curl-command", ""),
                    })
                except json.JSONDecodeError:
                    print(f"Error parsing JSON: {line}")
                except KeyError as e:
                    print(f"Missing key in result: {e}")
                    continue

            if not results_list:
                return JsonResponse({"message": "No vulnerabilities found.", "scan_id": None})

            # Save scan results
            try:
                scan_result = NucleiResult.objects.create(
                    user=request.user,
                    target=domain,
                    subdomain=subdomain,
                    bug_class=bug_class,
                    scan_results=json.dumps(results_list)
                )
                
                # Create activity record
                record_user_activity(
                    user=request.user,
                    activity_type='scan',
                    description=f'Vulnerability scan for {subdomain} ({bug_class})'
                )
                
                return JsonResponse({
                    "message": "Scan completed successfully!",
                    "results": results_list,
                    "scan_id": scan_result.id
                })
            except Exception as e:
                return JsonResponse({"status": "error", "message": f"Error saving results: {str(e)}"}, status=500)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@login_required
def get_subdomains(request):
    """Get all subdomains for a given domain"""
    domain = request.GET.get('domain')
    if domain:
        subdomains = ScanResult.objects.filter(user=request.user, target=domain).values_list('subdomains', flat=True)
        subdomain_list = []
        for subdomain_text in subdomains:
            if subdomain_text:
                subdomain_list.extend(subdomain_text.split("\n"))
        
        # Remove duplicates and empty strings
        subdomain_list = list(set(filter(None, subdomain_list)))
        return JsonResponse({"subdomains": subdomain_list})
    return JsonResponse({"error": "Domain not specified"}, status=400)

@login_required
def my_scans(request):
    """Show all previous scans"""
    scan_results = ScanResult.objects.filter(user=request.user).order_by('-created_at')
    
    if not scan_results.exists():
        # Return empty context if no results
        return render(request, 'my_scans.html', {'results': None})
    
    # Otherwise process and return the first result
    results = scan_results.first()
    subdomains = results.subdomains.split('\n') if results.subdomains else []
    
    # Filter out empty strings
    subdomains = list(filter(None, subdomains))
    
    # Create a context with all the needed information
    context = {
        'results': {
            'id': results.id,
            'target': results.target,
            'created_at': results.created_at,
            'r': subdomains
        }
    }
        
    return render(request, 'my_scans.html', context)

@login_required
def dashboard_view(request):
    """Display the main dashboard with scan results and statistics"""
    show_info = request.GET.get("show_info", "false").lower() == "true"
    # Fetch scan results only for the logged-in user
    scan_results = NucleiResult.objects.filter(user=request.user)

    # Extract unique scanned domains
    scanned_domains = list(scan_results.values_list("target", flat=True).distinct())

    # Initialize statistics
    total_scans = scan_results.count()
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    total_vulnerabilities = 0

    parsed_results = []
    info_results = []  # Separate list for 'info' severity findings

    # Process scan results
    for result in scan_results:
        try:
            results_data = json.loads(result.scan_results)  # Load JSON data

            for entry in results_data:
                severity = entry.get("severity", "info").lower()  # Normalize severity
                
                # Update severity counts
                if severity in severity_counts:
                    severity_counts[severity] += 1
                
                # Exclude 'info' from total_vulnerabilities count
                if severity != "info":
                    total_vulnerabilities += 1

                # Construct the vulnerability entry
                entry_dict = {
                    "id": result.id,
                    "target": result.target,
                    "subdomain": result.subdomain,
                    "bug_class": result.bug_class,
                    "severity": severity,
                    "url": entry.get("url", ""),
                    "vulnerability": entry.get("template_name", "Unknown Vulnerability"),
                    "tags": entry.get("tags", ""),
                    "details": entry.get("curl_command", "No details available"),
                    "timestamp": entry.get("timestamp", result.created_at.isoformat()),
                    "created_at": result.created_at
                }

                # Store findings separately based on severity
                if severity == "info":
                    info_results.append(entry_dict)
                else:
                    parsed_results.append(entry_dict)

        except json.JSONDecodeError:
            print(f"Invalid JSON in scan_results for id {result.id}")
            continue  # Skip if scan_results is not a valid JSON

    # Pass data to template
    context = {
        "scanned_domains": scanned_domains,
        "total_scans": total_scans,
        "total_vulnerabilities": total_vulnerabilities,
        "severity_counts": severity_counts,
        "parsed_results": parsed_results,
        "info_results": info_results if show_info else [],
        "show_info": show_info,
    }
    return render(request, "dashboard.html", context)

@login_required
def profile_view(request):
    """Display and manage user profile"""
    try:
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'completed_onboarding': False}
        )
        
        # Calculate account age in days
        account_age = (timezone.now() - request.user.date_joined).days
        
        # Get scan statistics
        total_scans = ScanResult.objects.filter(user=request.user).count()
        total_domains = ScanResult.objects.filter(user=request.user).values('target').distinct().count()
        total_vulnerabilities = NucleiResult.objects.filter(user=request.user).count()
        
        # Get recent activities with error handling
        try:
            activities = UserActivity.objects.filter(user=request.user)[:10]
        except Exception as e:
            print(f"Error fetching activities: {str(e)}")
            activities = []
        
        # Get API keys with error handling
        try:
            api_keys = ApiKey.objects.filter(user=request.user)
        except Exception as e:
            print(f"Error fetching API keys: {str(e)}")
            api_keys = []
        
        context = {
            'user': request.user,
            'profile': profile,
            'account_age': account_age,
            'total_scans': total_scans,
            'total_domains': total_domains,
            'total_vulnerabilities': total_vulnerabilities,
            'activities': activities,
            'api_keys': api_keys,
            'preferences': {
                'email_notifications': profile.email_notifications,
                'critical_alerts': profile.critical_alerts,
                'weekly_digest': profile.weekly_digest,
            }
        }
        
        return render(request, 'profile.html', context)
    except Exception as e:
        print(f"Profile view error: {str(e)}")
        messages.error(request, f"Could not load profile: {str(e)}")
        return render(request, 'profile.html', {'error': True})

@login_required
def update_profile(request):
    """Update user profile information"""
    if request.method == 'POST':
        try:
            # Get the profile object
            profile, created = UserProfile.objects.get_or_create(
                user=request.user,
                defaults={'completed_onboarding': False}
            )
            
            # Update user details
            user = request.user
            user.username = request.POST.get('username')
            user.email = request.POST.get('email')
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.save()
            
            # Update profile details
            profile.company = request.POST.get('company')
            profile.bio = request.POST.get('bio')
            profile.save()
            
            # Create activity record
            record_user_activity(
                user=request.user,
                activity_type='update',
                description='Updated profile information'
            )
            
            messages.success(request, 'Your profile has been updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
        
        return redirect('profile')
    
    return redirect('profile')

@login_required
def change_password(request):
    """Handle password changes"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            
            # Create activity record
            record_user_activity(
                user=request.user,
                activity_type='password',
                description='Changed password'
            )
            
            messages.success(request, 'Your password was successfully updated!')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    
    return redirect('profile')

@login_required
def update_preferences(request):
    """Update user preferences"""
    if request.method == 'POST':
        try:
            profile, created = UserProfile.objects.get_or_create(
                user=request.user,
                defaults={'completed_onboarding': False}
            )
            
            # Update notification preferences
            profile.email_notifications = 'email_notifications' in request.POST
            profile.critical_alerts = 'critical_alerts' in request.POST
            profile.weekly_digest = 'weekly_digest' in request.POST
            profile.save()
            
            # Create activity record
            record_user_activity(
                user=request.user,
                activity_type='update',
                description='Updated notification preferences'
            )
            
            messages.success(request, 'Your preferences have been updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating preferences: {str(e)}')
    
    return redirect('profile')

@login_required
def generate_api_key(request):
    """Generate a new API key and display it to the user"""
    try:
        # Generate a random key
        alphabet = string.ascii_letters + string.digits
        key = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        # Default name with timestamp
        name = f"API Key - {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Create new API key (no expiration by default)
        api_key = ApiKey.objects.create(
            user=request.user,
            name=name,
            key=key
        )
        
        # Create activity record
        record_user_activity(
            user=request.user,
            activity_type='update',
            description=f'Generated new API key: {name}'
        )
        
        # Instead of redirecting, render the dedicated template
        return render(request, 'api_key_created.html', {'api_key': api_key})
    except Exception as e:
        messages.error(request, f'Error generating API key: {str(e)}')
        return redirect('profile')
    
@login_required
def onboarding(request):
    """Handle user onboarding"""
    # Check if user has completed onboarding
    profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'completed_onboarding': False}
    )
    
    if profile.completed_onboarding:
        return redirect('dashboard')
    
    if request.method == 'POST' and 'complete_onboarding' in request.POST:
        # Mark onboarding as complete
        profile.completed_onboarding = True
        profile.save()
        
        # Create activity record
        record_user_activity(
            user=request.user,
            activity_type='update',
            description='Completed onboarding'
        )
        
        return redirect('dashboard')
    
    return render(request, 'onboarding.html')

@login_required
def help_center(request):
    """Display the help center page"""
    return render(request, 'help_center.html')

@csrf_exempt
def submit_feedback(request):
    """Handle user feedback submissions"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create feedback entry
            feedback = UserFeedback(
                user=request.user if request.user.is_authenticated else None,
                feedback_type=data.get('type'),
                rating=data.get('rating'),
                feedback_text=data.get('feedback'),
                contact_consent=data.get('contact_consent', False),
                email=data.get('email') if data.get('contact_consent') else None,
                page_url=data.get('page_url'),
                user_agent=data.get('user_agent')
            )
            feedback.save()
            
            return JsonResponse({"status": "success", "message": "Feedback submitted successfully!"})
            
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON data"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

@login_required
def global_search(request):
    """Global search functionality across domains, subdomains, and vulnerabilities"""
    query = request.GET.get('q', '')
    
    if not query:
        return render(request, 'search_results.html', {
            'query': query,
            'has_search': False,
            'domains': [],
            'subdomains': [],
            'vulnerabilities': [],
            'total_results': 0
        })
    
    # Search domains
    domains = ScanResult.objects.filter(
        user=request.user,
        target__icontains=query
    ).values('target').distinct()
    
    # Search subdomains
    subdomains_results = []
    scan_results = ScanResult.objects.filter(user=request.user)
    
    for scan in scan_results:
        subdomains = scan.subdomains.split('\n') if scan.subdomains else []
        matching_subdomains = [s for s in subdomains if query.lower() in s.lower() and s.strip()]
        if matching_subdomains:
            subdomains_results.append({
                'domain': scan.target,
                'subdomains': matching_subdomains
            })
    
    # Search vulnerabilities
    vulnerabilities = []
    nuclei_results = NucleiResult.objects.filter(
        user=request.user
    ).filter(
        Q(target__icontains=query) | 
        Q(subdomain__icontains=query) | 
        Q(bug_class__icontains=query) |
        Q(scan_results__icontains=query)
    )
    
    for result in nuclei_results:
        try:
            scan_data = json.loads(result.scan_results)
            for entry in scan_data:
                # Add relevant entries to vulnerabilities
                vulnerabilities.append({
                    'domain': result.target,
                    'subdomain': result.subdomain,
                    'vulnerability': entry.get('template_name', 'Unknown Vulnerability'),
                    'severity': entry.get('severity', 'unknown'),
                    'url': entry.get('url', ''),
                    'created_at': result.created_at,
                    'id': result.id
                })
        except json.JSONDecodeError:
            continue
    
    # Calculate total results
    subdomain_count = sum(len(item['subdomains']) for item in subdomains_results)
    total_results = len(domains) + subdomain_count + len(vulnerabilities)
    
    return render(request, 'search_results.html', {
        'query': query,
        'has_search': True,
        'domains': domains,
        'subdomains': subdomains_results,
        'vulnerabilities': vulnerabilities,
        'total_results': total_results
    })

@login_required
def report_dashboard(request):
    """View for displaying the interactive report dashboard"""
    log_request(request, "Report Dashboard Request")
    
    # Check if this is an AJAX request for data
    if request.GET.get('data') == 'json':
        log_data({"request_type": "AJAX", "params": dict(request.GET.items())}, "Processing AJAX Request")
        try:
            response = report_data_api(request)
            log_data({"status": "AJAX response generated"}, "AJAX Response Generated")
            return response
        except Exception as e:
            log_exception(e, "AJAX Request Error")
            return JsonResponse({
                'error': f"Error processing request: {str(e)}",
                'detail': traceback.format_exc()
            }, status=500)
    
    # Normal page load - render the dashboard template
    try:
        domains = ScanResult.objects.filter(user=request.user).values_list('target', flat=True).distinct()
        log_data({"domains_count": len(domains)}, "Found Domains")
        
        context = {
            'domains': domains,
        }
        
        return render(request, 'reports/dashboard.html', context)
    except Exception as e:
        log_exception(e, "Dashboard Render Error")
        return JsonResponse({
            'error': f"Error rendering dashboard: {str(e)}",
        }, status=500)

class DateTimeEncoder(DjangoJSONEncoder):
    """Extended JSON encoder that handles additional types"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

import os
import shutil
from django.http import JsonResponse

def check_paths(request):
    """Debug endpoint to check if required paths exist"""
    paths = {
        'SUBFINDER_PATH': shutil.which(SUBFINDER_PATH) is not None,
        'NUCLEI_PATH': shutil.which(NUCLEI_PATH) is not None,
        'NUCLEI_TEMPLATES_PATH': os.path.exists(NUCLEI_TEMPLATES_PATH),
        'TMP_RESULTS_PATH': os.path.exists(TMP_RESULTS_PATH),
        'BASE_RESULTS_DIR': os.path.exists(BASE_RESULTS_DIR)
    }
    
    # Also check specific template directories
    for bug_class, template_dir in BUG_CLASS_TEMPLATES.items():
        path = os.path.join(NUCLEI_TEMPLATES_PATH, template_dir)
        paths[f'Template: {bug_class}'] = os.path.exists(path)
    
    return JsonResponse(paths)