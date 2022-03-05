require('./style.scss');

let $ = require('cash-dom');
let bulmaToast = require('bulma-toast');

$('.navbar-burger').on('click', function (e) {
    $('.navbar-burger').toggleClass('is-active');
    $('.navbar-menu').toggleClass('is-active');
})

$('button').on('click', function (e) {
    $(this).addClass('is-loading');
});

$('button.delete').on('click', function (e) {
    $(this).parent().hide();
});

$('form').on('submit', async function (e) {
    e.preventDefault();

    const data = {};
    new FormData(e.target).forEach((value, key) => (data[key] = value));
    console.log(data);
    console.log(this.action);
    var resp = await(api({ action: this.action, ...data }));

    if (resp.hasOwnProperty('redirect') && resp.redirect === true) {
        window.location = 'http://' + data.domain;
    }

    toast(resp);
});

$('.button.toggle').on('click', async function (e) {
    var resp = await api({ 'action': 'toggle', 'state': this.id });
    $(this).parent().children().toggle();

    toast(resp);
});

async function api(body) {
    return fetch(document.location.origin + '/api', {
        method: 'POST',
        cache: 'no-cache',
        body: JSON.stringify(body)
    })
        .catch(error => console.log(error))
        .then(response => response.json())
}

function toast(message) {
    bulmaToast.toast(message);
    $('button.is-loading').removeClass('is-loading');
}

bulmaToast.setDefaults({ duration: 5000, extraClasses: 'force-border is-light', dismissible: true });
