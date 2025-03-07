// 等待页面加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 自动隐藏提示消息
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // 文本框字数统计
    var dreamContent = document.querySelector('#dream_content');
    if (dreamContent) {
        dreamContent.addEventListener('input', function() {
            var length = this.value.length;
            var minLength = 10;
            var maxLength = 1000;
            
            if (length < minLength) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            } else if (length > maxLength) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            } else {
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
            }
        });
    }

    // 提交表单时显示加载状态
    var forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            var submitBtn = this.querySelector('input[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.value = '处理中...';
            }
        });
    });
}); 