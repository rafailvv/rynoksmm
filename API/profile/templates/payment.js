let clientID;
let email;

try {
    clientID = window.Telegram.WebApp.initDataUnsafe.user.id;
} catch (error) {
    console.error('Error getting clientID from WebApp:', error);
    const urlParams = new URLSearchParams(window.location.search);
    const encodedId = urlParams.get('id');
    if (encodedId) {
        clientID = Number(atob(encodedId));
    } else {
        console.error('No clientID available.');
    }
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
    const urlParams = new URLSearchParams(window.location.search);
    const price = urlParams.get('price');
    const days = urlParams.get('days');
    const req = urlParams.get('req');

    if (!price || !days || !email) {
        console.error('Missing parameters: price, days, hours, or email.');
        return;
    }

    try {
        const response = await fetch('/payment/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                client_id: clientID,
                price: price,
                days: days,
                email: email,
                req: req
            })
        });

        if (!response.ok) {
            throw new Error('Failed to create payment.');
        }

        const data = await response.json();
        if (data.confirmation_token && data.id) {
            const checkout = new window.YooMoneyCheckoutWidget({
                confirmation_token: data.confirmation_token,
                return_url: 'https://rynoksmm.ru/templates/success.html?payment_id=' + data.id,
                error_callback: function(error) {
                    console.log(error);
                }
            });

            // Отображение платежной формы в контейнере
            checkout.render('payment-form');
            document.getElementById('payment-form').style.display = 'block';
        } else {
            console.error('Invalid response from server:', data);
        }

    } catch (error) {
        console.error('Error during payment creation:', error);
    }
}

document.getElementById('next-button').addEventListener('click', function() {
    email = document.getElementById('email').value;

    if (!email) {
        alert('Пожалуйста, введите ваш email.');
        return;
    }

    document.getElementById('email-container').style.display = 'none';
    document.querySelector('.button-container').style.display = 'none';
    createPayment();
});
