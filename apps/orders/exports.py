import openpyxl
from django.http import HttpResponse
from rest_framework.views import APIView
from .utils import get_filtered_orders
from rest_framework.permissions import IsAdminUser
from openpyxl.styles import Font
from django.db.models import Sum
from django.utils import timezone
from django.utils.timezone import localtime


class AdminOrderExportAPIView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self,request):
        
        orders = get_filtered_orders(request).prefetch_related('items')
        include_summary = request.query_params.get('summary') == 'true'
        
        wb = openpyxl.Workbook()
        ws_orders = wb.active
        ws_orders.title = 'Orders'
        
        orders_headers = [
            'Order Number',
            'Customer Number',
            'Phone',
            'Alternate Phone',
            'Status',
            'Total Amount',
            'Street',
            'City',
            'Landmark',
            'Pincode',
            'Created At',
        ]
        
        # For Orders sheet
        ws_orders.append(orders_headers)
        
        for cell in ws_orders[1]:
            cell.font = Font(bold=True)
        
        # For Order Items sheet
        ws_items = wb.create_sheet(title='Order Items')
        
        items_headers = [
            'Order Number',
            'Product',
            'Variant Weight',
            'Quantity',
            'Unit Price',
            'Total Price',
        ]
        
        ws_items.append(items_headers)
        
        for cell in ws_items[1]:
            cell.font = Font(bold=True)
        
        for order in orders:
            
            # Orders Sheet
            ws_orders.append([
                order.order_number,
                order.customer.name,
                order.customer.phone_no,
                order.customer.alternate_phone_no,
                order.order_status,
                order.total_amount,
                order.shipping_address.street if order.shipping_address else "",
                order.shipping_address.city if order.shipping_address else "",
                order.shipping_address.landmark if order.shipping_address else "",
                order.shipping_address.pincode if order.shipping_address else "",
                order.created_at.strftime('%Y-%m-%d %H:%M'),
            ])
            
            # Items Sheet
            
            for item in order.items.all():
                ws_items.append([
                    order.order_number,
                    item.product_name,
                    item.variant_weight,
                    item.quantity,
                    item.unit_price,
                    item.total_price,
                ])
            
        # optional Summary sheet   
        if include_summary:
            
            ws_summary = wb.create_sheet(title='Summary')
            
            
            # Metrics section
            
            total_orders = orders.count()
            confirmed_orders = orders.filter(order_status='confirmed').count()
            pending_orders = orders.filter(order_status='pending').count()
            cancelled_orders = orders.filter(order_status='cancelled').count()
            revenue = orders.filter(order_status='confirmed').aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            pending_value = orders.filter(order_status='pending').aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            cancelled_value = orders.filter(order_status='cancelled_value').aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            conversion_rate = (confirmed_orders / total_orders) * 100 if total_orders else 0
            
            
            
            ws_summary.append(['Metrics', 'Value'])
            ws_summary.append(['Total Orders', total_orders])
            ws_summary.append(['Confirmed Orders', confirmed_orders])
            ws_summary.append(['Pending Orders', pending_orders])
            ws_summary.append(['Cancelled Orders', cancelled_orders])
            ws_summary.append(['Revenue', revenue])
            ws_summary.append(['Pending Value', pending_value])
            ws_summary.append(['Cancelled Value', cancelled_value])
            ws_summary.append(['Conversion Rate', conversion_rate])
            
            
            ws_summary.append([])
            ws_summary.append([])
            
            status = request.query_params.get('status')
            search = request.query_params.get('search')
            date = request.query_params.get('date')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            quick = request.query_params.get('quick')
            min_amount = request.query_params.get('min_amount')
            max_amount = request.query_params.get('max_amount')
            
            # Filters Section
            
            ws_summary.append(["Filters Used",""])
            ws_summary.append(["Status", status or "All"])
            ws_summary.append(["Search", search or "None"])
            ws_summary.append(["Date", date or "None"])
            ws_summary.append(["Start Date", start_date or "None"])
            ws_summary.append(["End Date", end_date or "None"])
            ws_summary.append(["Quick Filter", quick or "None"])
            ws_summary.append(["Min Amount", min_amount or "None"])
            ws_summary.append(["Max Amount", max_amount or "None"])
            
             
            ws_summary.append([])
        
            ws_summary.append(["Export Generated At", localtime(timezone.now()).strftime("%Y-%m-%d %H:%M")])
            
            
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        response['Content-Disposition'] = 'attachment; filename="orders.xlsx"'
        
        wb.save(response)
        
        return response