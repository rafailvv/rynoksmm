let email;
let paymentType;
let paymentPlanId;
let paymentPlan;
let telegramInitData = "";


function syncFullscreenOffset(webApp) {
    const isFullscreen = Boolean(webApp && webApp.isFullscreen);
    document.body.classList.toggle('tg-fullscreen', isFullscreen);
}

function shouldUseMobileFullscreen(webApp) {
    const userAgent = navigator.userAgent.toLowerCase();
    const platform = String((webApp && webApp.platform) || '').toLowerCase();
    return (
        userAgent.includes('android') ||
        userAgent.includes('iphone') ||
        userAgent.includes('ipad') ||
        userAgent.includes('ipod') ||
        platform === 'android' ||
        platform === 'ios'
    );
}

function getElements() {
    return {
        priceValue: document.getElementById('price-value'),
        periodValue: document.getElementById('period-value'),
        daysValue: document.getElementById('days-value'),
        typeValue: document.getElementById('type-value'),
        planLabel: document.getElementById('plan-label'),
        planBadge: document.getElementById('plan-badge'),
        statusMessage: document.getElementById('status-message'),
        widgetCaption: document.getElementById('widget-caption'),
        nextButton: document.getElementById('next-button'),
        emailContainer: document.getElementById('email-container'),
        paymentForm: document.getElementById('payment-form')
    };
}

function formatPrice(value) {
    return `${Number(value || 0).toLocaleString('ru-RU')} ₽`;
}

function isValidEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function pluralizeDays(days) {
    const mod10 = days % 10;
    const mod100 = days % 100;

    if (mod10 === 1 && mod100 !== 11) {
        return `${days} день`;
    }
    if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
        return `${days} дня`;
    }
    return `${days} дней`;
}

function getPaymentCopy(req, days) {
    if (req === 'subscription') {
        return {
            label: 'Подписка',
            badge: 'Публикация карточки специалиста',
            type: 'Подписка',
            period: `на ${pluralizeDays(days)}`,
            caption: 'После оплаты откроется защищенный виджет YooKassa для активации подписки.'
        };
    }

    return {
        label: 'Пакет запросов',
        badge: 'Разовое пополнение',
        type: 'Покупка запросов',
        period: `${days} запросов`,
        caption: 'После оплаты откроется защищенный виджет YooKassa для пополнения баланса запросов.'
    };
}

function setStatus(message, isError = false) {
    const { statusMessage } = getElements();
    statusMessage.textContent = message;
    statusMessage.classList.toggle('error', isError);
}

function getTelegramHeaders(extraHeaders = {}) {
    if (!telegramInitData) {
        return extraHeaders;
    }

    return {
        ...extraHeaders,
        'X-Telegram-Init-Data': telegramInitData,
    };
}

async function renderPurchaseSummary() {
    const { nextButton } = getElements();
    const urlParams = new URLSearchParams(window.location.search);
    paymentPlanId = urlParams.get('plan');

    if (!paymentPlanId) {
        setStatus('Не удалось определить тариф оплаты.', true);
        nextButton.disabled = true;
        return;
    }

    if (!telegramInitData) {
        setStatus('Откройте оплату из Telegram, чтобы продолжить.', true);
        nextButton.disabled = true;
        return;
    }

    const response = await fetch(`/payment/plan/${encodeURIComponent(paymentPlanId)}`, {
        headers: getTelegramHeaders(),
    });
    if (!response.ok) {
        throw new Error('Failed to load payment plan');
    }

    paymentPlan = await response.json();
    const price = Number(paymentPlan.price || 0);
    const days = Number(paymentPlan.days || 0);
    paymentType = paymentPlan.req || 'subscription';

    const copy = getPaymentCopy(paymentType, days);
    const {
        priceValue,
        periodValue,
        daysValue,
        typeValue,
        planLabel,
        planBadge,
        widgetCaption
    } = getElements();

    priceValue.textContent = formatPrice(price);
    periodValue.textContent = copy.period;
    daysValue.textContent = paymentType === 'subscription' ? pluralizeDays(days) : `${days} шт.`;
    typeValue.textContent = copy.type;
    planLabel.textContent = copy.label;
    planBadge.textContent = copy.badge;
    if (widgetCaption) {
        widgetCaption.textContent = copy.caption;
    }

    nextButton.disabled = false;
}

document.addEventListener('touchstart', function(event) {
    const activeElement = document.activeElement;

    if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
        if (!activeElement.contains(event.target)) {
            activeElement.blur();
        }
    }
});

async function createPayment() {
    if (!paymentPlan || !paymentPlanId || !email || !telegramInitData) {
        console.error('Missing parameters: plan or email.');
        return;
    }

    try {
        const response = await fetch('/payment/token', {
            method: 'POST',
            headers: getTelegramHeaders({
                'Content-Type': 'application/json',
            }),
            body: JSON.stringify({
                plan: paymentPlanId,
                email: email,
            })
        });

        if (!response.ok) {
            throw new Error('Failed to create payment.');
        }

        const data = await response.json();
        if (data.confirmation_token && data.id) {
            const returnUrl = `${window.location.origin}/templates/success.html?payment_id=${data.id}`;
            const checkout = new window.YooMoneyCheckoutWidget({
                confirmation_token: data.confirmation_token,
                return_url: returnUrl,
                error_callback: function(error) {
                    console.log(error);
                }
            });

            checkout.render('payment-form');
            const { paymentForm } = getElements();
            paymentForm.style.display = 'block';
            setStatus('Платежный виджет загружен. Проверьте данные карты и завершите оплату.');
        } else {
            console.error('Invalid response from server:', data);
            setStatus('Не удалось подготовить оплату. Попробуйте еще раз.', true);
            getElements().nextButton.disabled = false;
        }

    } catch (error) {
        console.error('Error during payment creation:', error);
        setStatus('Ошибка при создании платежа. Попробуйте снова чуть позже.', true);
        getElements().nextButton.disabled = false;
    }
}

document.getElementById('next-button').addEventListener('click', function() {
    email = document.getElementById('email').value.trim();
    const { nextButton } = getElements();

    if (!email) {
        setStatus('Укажите email, чтобы мы могли отправить чек.', true);
        return;
    }

    if (!isValidEmail(email)) {
        setStatus('Похоже, email введен в неверном формате.', true);
        return;
    }

    setStatus('Подготавливаем защищенную форму оплаты...');
    nextButton.disabled = true;
    createPayment();
});

try {
    const webApp = window.Telegram && window.Telegram.WebApp;
    telegramInitData = webApp && webApp.initData ? webApp.initData : '';
    syncFullscreenOffset(webApp);
    if (webApp && typeof webApp.onEvent === 'function') {
        webApp.onEvent('fullscreenChanged', function() {
            syncFullscreenOffset(webApp);
        });
        webApp.onEvent('viewportChanged', function() {
            syncFullscreenOffset(webApp);
        });
    }
    if (shouldUseMobileFullscreen(webApp) && typeof webApp.requestFullscreen === 'function') {
        webApp.requestFullscreen();
        setTimeout(function() {
            syncFullscreenOffset(webApp);
        }, 150);
    }
} catch (error) {
    console.error('Error getting initData from WebApp:', error);
}

renderPurchaseSummary().catch((error) => {
    console.error('Error loading payment plan:', error);
    setStatus('Не удалось загрузить параметры оплаты. Откройте экран заново из Telegram.', true);
    getElements().nextButton.disabled = true;
});
