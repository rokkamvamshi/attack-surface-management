# reports.py - Add this file to your ASMapp folder

import json
import csv
import io
from datetime import datetime
from collections import Counter
import base64
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.contrib.auth.decorators import login_required
# from weasyprint import HTML, CSS
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .debug_utils import log_request, log_data, log_exception
import traceback
from .models import ScanResult, NucleiResult, UserActivity

from django.core.serializers.json import DjangoJSONEncoder
import json
from django.http import JsonResponse


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

class ReportGenerator:
    """Class for generating various security reports"""
    
    def __init__(self, user, domain=None, start_date=None, end_date=None):
        """Initialize with user and optional filters"""
        self.user = user
        self.domain = domain
        self.start_date = start_date
        self.end_date = end_date
        self.report_data = {}
        
    def generate_report_data(self):
        """Generate comprehensive report data with serializable outputs"""
        # Collect base data
        self._collect_base_data()
        
        # Collect vulnerability data
        self._collect_vulnerability_data()
        
        # Generate additional insights
        self._generate_insights()
        
        # Convert dates to strings to ensure JSON serialization
        if 'generation_date' in self.report_data:
            self.report_data['generation_date'] = self.report_data['generation_date'].isoformat()
        
        if 'scans' in self.report_data and self.report_data['scans'].get('latest'):
            latest = self.report_data['scans']['latest']
            if hasattr(latest, 'created_at'):
                self.report_data['scans']['latest'] = {
                    'id': latest.id,
                    'target': latest.target,
                    'created_at': latest.created_at.isoformat()
                }
        
        if 'scans' in self.report_data and self.report_data['scans'].get('first'):
            first = self.report_data['scans']['first']
            if hasattr(first, 'created_at'):
                self.report_data['scans']['first'] = {
                    'id': first.id,
                    'target': first.target, 
                    'created_at': first.created_at.isoformat()
                }
        
        # Ensure all vulnerability data is serializable
        if 'vulnerabilities' in self.report_data and 'list' in self.report_data['vulnerabilities']:
            for vuln in self.report_data['vulnerabilities']['list']:
                if isinstance(vuln.get('scan_date'), datetime):
                    vuln['scan_date'] = vuln['scan_date'].isoformat()
        
        return self.report_data
    
    def _collect_base_data(self):
        """Collect basic scan data and statistics"""
        # Build query filters
        filters = {'user': self.user}
        if self.domain:
            filters['target'] = self.domain
            
        date_filters = {}
        if self.start_date:
            date_filters['created_at__gte'] = self.start_date
        if self.end_date:
            date_filters['created_at__lte'] = self.end_date
            
        # Get domain scan data
        domain_scans = ScanResult.objects.filter(**filters, **date_filters)
        
        # Get subdomains from all scans
        subdomains = []
        if domain_scans:
            for scan in domain_scans:
                if scan.subdomains:
                    subdomains.extend(scan.subdomains.strip().split('\n'))
            
            # Remove duplicates and empty strings
            subdomains = list(set(filter(None, subdomains)))
        
        # Store data in report
        self.report_data.update({
            'user': self.user.username,
            'generation_date': datetime.now(),
            'domain': self.domain,
            'scans': {
                'count': domain_scans.count(),
                'latest': domain_scans.order_by('-created_at').first(),
                'first': domain_scans.order_by('created_at').first(),
            },
            'subdomains': {
                'count': len(subdomains),
                'list': subdomains
            }
        })
    
    def _collect_vulnerability_data(self):
        """Collect vulnerability scan data"""
        # Build query filters
        filters = {'user': self.user}
        if self.domain:
            filters['target'] = self.domain
            
        date_filters = {}
        if self.start_date:
            date_filters['created_at__gte'] = self.start_date
        if self.end_date:
            date_filters['created_at__lte'] = self.end_date
        
        # Get vulnerability data
        vuln_results = NucleiResult.objects.filter(**filters, **date_filters)
        
        # Parse vulnerabilities from JSON data
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        vulnerability_types = []
        vulnerability_list = []
        
        for result in vuln_results:
            try:
                scan_data = json.loads(result.scan_results)
                
                for entry in scan_data:
                    # Extract severity and update counts
                    severity = entry.get("severity", "info").lower()
                    if severity in severity_counts:
                        severity_counts[severity] += 1
                    
                    # Extract vulnerability type
                    vuln_type = entry.get("template_name", "Unknown")
                    vulnerability_types.append(vuln_type)
                    
                    # Add to full vulnerability list
                    vulnerability_list.append({
                        'id': result.id,
                        'target': result.target,
                        'subdomain': result.subdomain,
                        'vulnerability': vuln_type,
                        'severity': severity,
                        'url': entry.get('url', ''),
                        'details': entry.get('curl_command', 'No details available'),
                        'timestamp': entry.get('timestamp', result.created_at.isoformat()),
                        'scan_date': result.created_at
                    })
            
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Count vulnerability types
        vuln_type_counts = dict(Counter(vulnerability_types))
        
        # Store vulnerability data in report
        self.report_data.update({
            'vulnerabilities': {
                'count': sum(severity_counts.values()),
                'by_severity': severity_counts,
                'by_type': vuln_type_counts,
                'list': vulnerability_list
            }
        })
    
    def _generate_insights(self):
        """Generate additional insights based on collected data"""
        vulnerabilities = self.report_data.get('vulnerabilities', {})
        severity_counts = vulnerabilities.get('by_severity', {})
        
        # Calculate risk score (weighted sum of severities)
        risk_score = (
            severity_counts.get('critical', 0) * 100 +
            severity_counts.get('high', 0) * 40 +
            severity_counts.get('medium', 0) * 10 +
            severity_counts.get('low', 0) * 1
        )
        
        # Calculate risk level based on score
        risk_level = 'Low'
        if risk_score > 500:
            risk_level = 'Critical'
        elif risk_score > 200:
            risk_level = 'High' 
        elif risk_score > 50:
            risk_level = 'Medium'
        
        # Calculate most vulnerable subdomains
        subdomain_vulnerability_counts = {}
        for vuln in vulnerabilities.get('list', []):
            subdomain = vuln.get('subdomain')
            if subdomain:
                if subdomain not in subdomain_vulnerability_counts:
                    subdomain_vulnerability_counts[subdomain] = {
                        'total': 0,
                        'critical': 0,
                        'high': 0,
                        'medium': 0,
                        'low': 0,
                        'info': 0
                    }
                
                subdomain_vulnerability_counts[subdomain]['total'] += 1
                severity = vuln.get('severity', 'info')
                if severity in subdomain_vulnerability_counts[subdomain]:
                    subdomain_vulnerability_counts[subdomain][severity] += 1
        
        # Sort subdomains by total vulnerabilities
        sorted_subdomains = sorted(
            subdomain_vulnerability_counts.items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )
        
        # Get top 5 most vulnerable subdomains
        top_vulnerable_subdomains = sorted_subdomains[:5]
        
        # Store insights in report
        self.report_data.update({
            'insights': {
                'risk_score': risk_score,
                'risk_level': risk_level,
                'most_vulnerable_subdomains': dict(top_vulnerable_subdomains),
                'most_common_vulnerabilities': dict(
                    sorted(
                        vulnerabilities.get('by_type', {}).items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                )
            }
        })
    
    def generate_executive_summary(self):
        """Generate an executive summary from the report data"""
        if not self.report_data:
            self.generate_report_data()
        
        vulnerabilities = self.report_data.get('vulnerabilities', {})
        insights = self.report_data.get('insights', {})
        
        summary = {
            'domain': self.domain,
            'scan_date': self.report_data.get('generation_date'),
            'subdomains_count': self.report_data.get('subdomains', {}).get('count', 0),
            'total_vulnerabilities': vulnerabilities.get('count', 0),
            'critical_count': vulnerabilities.get('by_severity', {}).get('critical', 0),
            'high_count': vulnerabilities.get('by_severity', {}).get('high', 0),
            'risk_level': insights.get('risk_level', 'Unknown'),
            'risk_score': insights.get('risk_score', 0),
            'top_vulnerabilities': list(insights.get('most_common_vulnerabilities', {}).keys())[:3],
            'top_vulnerable_subdomains': list(insights.get('most_vulnerable_subdomains', {}).keys())[:3]
        }
        
        return summary
    
    def generate_charts_data(self):
        """Generate data for charts and visualizations"""
        vulnerabilities = self.report_data.get('vulnerabilities', {})
        insights = self.report_data.get('insights', {})
        
        charts_data = {
            'severity_distribution': [
                {'name': 'Critical', 'value': vulnerabilities.get('by_severity', {}).get('critical', 0)},
                {'name': 'High', 'value': vulnerabilities.get('by_severity', {}).get('high', 0)},
                {'name': 'Medium', 'value': vulnerabilities.get('by_severity', {}).get('medium', 0)},
                {'name': 'Low', 'value': vulnerabilities.get('by_severity', {}).get('low', 0)},
                {'name': 'Info', 'value': vulnerabilities.get('by_severity', {}).get('info', 0)}
            ],
            'top_vulnerabilities': [
                {'name': vuln_type, 'value': count}
                for vuln_type, count in insights.get('most_common_vulnerabilities', {}).items()
            ][:5],
            'top_vulnerable_subdomains': [
                {
                    'name': subdomain, 
                    'critical': data.get('critical', 0),
                    'high': data.get('high', 0),
                    'medium': data.get('medium', 0),
                    'low': data.get('low', 0),
                    'info': data.get('info', 0)
                }
                for subdomain, data in insights.get('most_vulnerable_subdomains', {}).items()
            ][:5]
        }
        
        return charts_data
    
    def export_as_json(self):
        """Export report data as JSON"""
        if not self.report_data:    
            self.generate_report_data()
        
        # Create JSON response
        json_data = json.dumps(self.report_data, default=str, indent=4)
        response = HttpResponse(json_data, content_type='application/json')
        
        # Generate filename
        domain_slug = slugify(self.domain) if self.domain else 'all-domains'
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"security_report_{domain_slug}_{date_str}.json"
        
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    def export_as_pdf(self):
        """Temporary replacement until WeasyPrint is properly installed"""
        # For now, return the JSON version instead
        return self.export_as_json()
    
    def export_as_csv(self):
        """Export vulnerability findings as CSV"""
        if not self.report_data:
            self.generate_report_data()
        
        # Create a string buffer
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header row
        writer.writerow([
            'Domain', 'Subdomain', 'Vulnerability', 'Severity', 
            'URL', 'Details', 'Scan Date'
        ])
        
        # Write vulnerability data
        for vuln in self.report_data.get('vulnerabilities', {}).get('list', []):
            writer.writerow([
                vuln.get('target', ''),
                vuln.get('subdomain', ''),
                vuln.get('vulnerability', ''),
                vuln.get('severity', ''),
                vuln.get('url', ''),
                vuln.get('details', ''),
                vuln.get('scan_date', '')
            ])
        
        # Create response
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        
        # Generate filename
        domain_slug = slugify(self.domain) if self.domain else 'all-domains'
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"security_findings_{domain_slug}_{date_str}.csv"
        
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# View Functions

@login_required
def generate_report(request):
    """View for generating and downloading security reports"""
    # Get report parameters
    domain = request.GET.get('domain')
    report_type = request.GET.get('type', 'pdf')
    
    # Parse date range if provided
    start_date = None
    end_date = None
    date_range = request.GET.get('date_range')
    if date_range:
        try:
            start_str, end_str = date_range.split(' - ')
            start_date = datetime.strptime(start_str.strip(), '%Y-%m-%d')
            end_date = datetime.strptime(end_str.strip(), '%Y-%m-%d')
        except (ValueError, AttributeError):
            pass
    
    # Create report generator
    report_generator = ReportGenerator(
        user=request.user,
        domain=domain,
        start_date=start_date,
        end_date=end_date
    )
    
    # Generate report based on type
    if report_type == 'pdf':
        return report_generator.export_as_pdf()
    elif report_type == 'json':
        return report_generator.export_as_json()
    elif report_type == 'csv':
        return report_generator.export_as_csv()
    else:
        # Default to PDF
        return report_generator.export_as_pdf()

@login_required
def report_builder(request):
    """View for the report builder interface"""
    # Get list of all domains scanned by user
    domains = ScanResult.objects.filter(user=request.user).values_list('target', flat=True).distinct()
    
    context = {
        'domains': domains
    }
    
    return render_to_string('reports/report_builder.html', context)

# API endpoints for report generation

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def report_data_api(request):
    """API endpoint for getting report data"""
    log_request(request, "Report Data API Request")
    
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return json_response({'error': 'Authentication required'}, status=401)
    
    # Get report parameters
    domain = request.GET.get('domain')
    log_data({"domain_param": domain}, "Domain parameter")
    
    # Parse date range if provided
    start_date = None
    end_date = None
    date_range = request.GET.get('date_range')
    if date_range:
        try:
            start_str, end_str = date_range.split(' - ')
            start_date = datetime.strptime(start_str.strip(), '%Y-%m-%d')
            end_date = datetime.strptime(end_str.strip(), '%Y-%m-%d')
            log_data({"date_range": date_range, "start": start_str, "end": end_str}, "Date range parsed")
        except (ValueError, AttributeError) as e:
            log_exception(e, "Date parsing error")
    
    try:
        # Create report generator
        from .reports import ReportGenerator
        report_generator = ReportGenerator(
            user=request.user,
            domain=domain,
            start_date=start_date,
            end_date=end_date
        )
        
        log_data({"message": "Created report generator"}, "Report Generator")
        
        # Generate report data
        report_data = report_generator.generate_report_data()
        log_data({"message": "Generated report data"}, "Report Data")
        
        # Get executive summary
        summary = report_generator.generate_executive_summary()
        log_data({"message": "Generated executive summary"}, "Executive Summary")
        
        # Get charts data
        charts_data = report_generator.generate_charts_data()
        log_data({"message": "Generated charts data"}, "Charts Data")
        
        # Create response
        return json_response({
            'report': report_data,
            'summary': summary,
            'charts': charts_data
        })
    except Exception as e:
        log_exception(e, "Report Data API Error")
        return json_response({
            'error': f"Error generating report: {str(e)}",
            'detail': traceback.format_exc()
        }, status=500)
    
    
# Helper function for JSON serialization
def json_serializable(obj):
    """Convert objects to JSON serializable format"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj)

