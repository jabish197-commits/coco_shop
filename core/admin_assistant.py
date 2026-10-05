from .gemini_assistant import classify
from django.core.cache import cache
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from orders.models import Order
from shop.models import Product


@staff_member_required
@require_POST
def assistant(request):
    question = request.POST.get('question', '').strip().lower()
    if not question or len(question) > 500:
        return JsonResponse({'answer': 'Please enter a question of 1–500 characters.'}, status=400)
    if not (request.user.has_perm('orders.view_order') or request.user.has_perm('shop.view_product')):
        return JsonResponse({'answer': 'Permission denied.'}, status=403)
    if 'stock' in question:
        if not request.user.has_perm('shop.view_product'):
            return JsonResponse({'answer': 'Permission denied.'}, status=403)
        products = Product.objects.all()
        if 'out of stock' in question:
            products = products.filter(stock_quantity=0)
        elif 'low stock' in question:
            products = products.filter(stock_quantity__gt=0, stock_quantity__lte=5)
        else:
            matches = [p.pk for p in products if p.name.lower() in question.lower()]
            if matches:
                products = products.filter(pk__in=matches)
        total = sum(p.stock_quantity for p in products)
        lines = [f'Available stock: {total} units across {products.count()} products.']
        lines += [f'{p.name}: {p.stock_quantity} available' for p in products[:30]]
        if products.count() > 30:
            lines.append('Showing first 30 products. See Products for all stock quantities.')
        return JsonResponse({'answer': '\n'.join(lines)})
    if not cache.add(f'admin-chat-{request.user.pk}', True, timeout=3):
        return JsonResponse({'answer': 'Please wait a few seconds before asking again.'}, status=429)
    direct_questions = {
        'orders': 'total orders',
        'order count': 'total orders',
        'how many orders': 'total orders',
        'how many orders are there': 'total orders',
        'show orders': 'total orders',
        'products': 'list products',
        'show products': 'list products',
        'how many products': 'product count',
        'how many products are there': 'product count',
        'how many orders today': 'today orders',
        'today pending orders': 'today pending orders',
        'today paid orders': 'today paid orders',
        'unpaid orders': 'pending orders',
        'total orders': 'total orders',
        'today orders': 'today orders',
        "today's orders": 'today orders',
        'today’s orders': 'today orders',
        'pending orders': 'pending orders',
        'paid orders': 'paid orders',
        'failed orders': 'failed orders',
        'expired orders': 'expired orders',
        'list products': 'list products',
        'product count': 'product count',
        'list active products': 'list active products',
        'list inactive products': 'list inactive products',
    }
    normalized = ' '.join(question.split()).rstrip('?!.,')
    if normalized in direct_questions:
        question = direct_questions[normalized]
    else:
        try:
            question = classify(question)
        except ValueError as error:
            return JsonResponse({'answer': str(error)}, status=503)
    tamil = False
    if any(w in question for w in ('order', 'ஆர்டர்', 'ஆர்டர', 'விற்பனை')):
        if not request.user.has_perm('orders.view_order'):
            return JsonResponse({'answer': 'You do not have permission to view orders.'}, status=403)
        orders = Order.objects.all()
        today = any(w in question for w in ('today', 'இன்று', 'இன்றைய', 'இன்னைக்கு'))
        if today:
            orders = orders.filter(created_at__date=timezone.localdate())
        status = next((s for s, words in [('pending', ('pending', 'unpaid', 'நிலுவை')), ('paid', ('paid', 'செலுத்திய')), ('failed', ('failed', 'தோல்வி')), ('expired', ('expired', 'காலாவதி'))] if any(w in question for w in words)), None)
        if status:
            orders = orders.filter(status=status)
        total = orders.count()
        label = ('இன்றைய' if today else 'மொத்த') if tamil else ('Today’s' if today else 'Total')
        lines = [f'{label} orders: {total}' + (f' ({status})' if status else '')]
        if not status:
            lines += [f'{name}: {orders.filter(status=value).count()}' for value, name in Order.Status.choices]
        lines.append(('தேதி கணக்கீடு: ' if tamil else 'Date timezone: ') + timezone.get_current_timezone_name())
        return JsonResponse({'answer': '\n'.join(lines)})
    if any(w in question for w in ('product', 'chocolate', 'பொருட்', 'பொருள்', 'புராடக்ட்', 'ப்ராடக்ட்', 'சாக்லேட்')):
        if not request.user.has_perm('shop.view_product'):
            return JsonResponse({'answer': 'You do not have permission to view products.'}, status=403)
        products = Product.objects.select_related('category').all()
        if 'inactive' in question:
            products = products.filter(active=False)
        elif 'active' in question:
            products = products.filter(active=True)
        lines = [('மொத்த products: ' if tamil else 'Total products: ') + str(products.count())]
        if not any(w in question for w in ('count', 'how many', 'எத்தனை', 'எவ்வளவு')):
            lines = [f'{p.name} — Quantity: {p.stock_quantity}' for p in products[:30]]
            if not lines:
                lines = ['No products found.']
            if products.count() > 30:
                lines.append('Showing the first 30 products. Use the Products admin page for the full list.')
        return JsonResponse({'answer': '\n'.join(lines)})
    return JsonResponse({'answer': 'Try: Total orders, Today’s orders, Pending orders, List products, Product count.\nThis assistant supports these topics only; it does not change records.'})


