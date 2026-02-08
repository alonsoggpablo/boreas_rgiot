// device_monitoring_client_filter.js
document.addEventListener('DOMContentLoaded', function() {
    var clientField = document.querySelector('select[name="client_name"]');
    var deviceField = document.querySelector('select[name="external_device"]');
    if (!clientField || !deviceField) return;

    clientField.addEventListener('change', function() {
        var client = clientField.value;
        deviceField.innerHTML = '';
        var emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = '---------';
        deviceField.appendChild(emptyOption);
        if (!client) return;
        fetch('/admin/boreas_mediacion/externaldevicemapping/?client_name=' + encodeURIComponent(client))
            .then(response => response.json())
            .then(data => {
                data.results.forEach(function(device) {
                    var option = document.createElement('option');
                    option.value = device.id;
                    option.textContent = device.external_alias || device.external_device_id;
                    deviceField.appendChild(option);
                });
            });
    });
});