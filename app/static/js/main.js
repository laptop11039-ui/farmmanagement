// Main JavaScript file

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Format currency on input
    const currencyInputs = document.querySelectorAll('input[type="number"][name*="price"], input[type="number"][name*="rate"]');
    currencyInputs.forEach(input => {
        input.addEventListener('blur', function() {
            this.value = parseFloat(this.value).toFixed(2);
        });
    });

    // Auto-calculate total
    const quantityInput = document.querySelector('input[name="quantity"]');
    const priceInput = document.querySelector('input[name="price_per_unit_usd"]');
    
    if (quantityInput && priceInput) {
        [quantityInput, priceInput].forEach(input => {
            input.addEventListener('change', calculateTotal);
        });
    }

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('هل أنت متأكد من الحذف؟')) {
                e.preventDefault();
            }
        });
    });

    // Add active class to current nav link
    const currentLocation = location.pathname;
    const menuItems = document.querySelectorAll('.navbar-nav a');
    menuItems.forEach(item => {
        if (item.pathname === currentLocation) {
            item.classList.add('active');
        }
    });
});

// Calculate total function
function calculateTotal() {
    const quantity = parseFloat(document.querySelector('input[name="quantity"]').value) || 0;
    const price = parseFloat(document.querySelector('input[name="price_per_unit_usd"]').value) || 0;
    const totalInput = document.querySelector('input[name="total"]');
    
    if (totalInput) {
        totalInput.value = (quantity * price).toFixed(2);
    }
}

// Delete product function (used in settings)
function deleteProduct(productId) {
    if (confirm('هل أنت متأكد من حذف هذا المنتج؟')) {
        fetch(`/settings/product_type/${productId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const row = document.getElementById(`product-${productId}`);
                if (row) {
                    row.style.animation = 'fadeOut 0.3s ease';
                    setTimeout(() => row.remove(), 300);
                }
                showAlert('تم حذف المنتج بنجاح', 'success');
            } else {
                showAlert('حدث خطأ في الحذف', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('حدث خطأ', 'danger');
        });
    }
}

// Show alert notification
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        alertDiv.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}

// Format currency display
function formatCurrency(amount, currency = 'USD') {
    const formatter = new Intl.NumberFormat('ar-LB', {
        style: 'currency',
        currency: currency === 'LBP' ? 'LBP' : 'USD'
    });
    return formatter.format(amount);
}

// Edit production (placeholder)
function editProduction(productionId) {
    alert('وظيفة التعديل قيد التطوير');
}

// Export table to CSV
function exportTableToCSV(filename = 'export.csv') {
    const csv = [];
    const table = document.querySelector('table');
    
    if (!table) return;
    
    // Get headers
    const headers = [];
    table.querySelectorAll('thead th').forEach(th => {
        headers.push(th.textContent.trim());
    });
    csv.push(headers.join(','));
    
    // Get rows
    table.querySelectorAll('tbody tr').forEach(tr => {
        const row = [];
        tr.querySelectorAll('td').forEach(td => {
            row.push('"' + td.textContent.trim().replace(/"/g, '""') + '"');
        });
        csv.push(row.join(','));
    });
    
    // Create and download
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Fade out animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-20px);
        }
    }
`;
document.head.appendChild(style);
