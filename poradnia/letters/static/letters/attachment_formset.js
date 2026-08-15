function replaceAttachmentDeleteCheckbox(row, deleteText) {
    var checkbox = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
    if (!checkbox) {
        return;
    }
    var cell = checkbox.closest('td');
    if (!cell) {
        return;
    }
    var hidden = document.createElement('input');
    hidden.type = 'hidden';
    hidden.name = checkbox.name;
    hidden.id = checkbox.id;
    cell.querySelectorAll('label[for="' + checkbox.id + '"]').forEach(function (label) {
        label.style.display = 'none';
    });
    checkbox.replaceWith(hidden);

    var link = document.createElement('a');
    link.href = 'javascript:void(0)';
    link.className = 'delete-row';
    link.textContent = deleteText;
    link.addEventListener('click', function () {
        hidden.value = 'on';
        row.style.display = 'none';
    });
    cell.appendChild(link);
}

function initAttachmentFormset(tbody, options) {
    if (!tbody) {
        return;
    }
    var emptyRow = tbody.querySelector('tr.empty-form');
    if (!emptyRow) {
        return;
    }
    var prefixInput = emptyRow.querySelector('[name*="-__prefix__-"]');
    if (!prefixInput) {
        return;
    }
    var prefix = prefixInput.name.split('-__prefix__-')[0];
    var totalForms = document.getElementById('id_' + prefix + '-TOTAL_FORMS');
    if (!totalForms) {
        return;
    }

    tbody.querySelectorAll('tr').forEach(function (row) {
        if (row !== emptyRow) {
            replaceAttachmentDeleteCheckbox(row, options.deleteText);
        }
    });

    var addRow = document.createElement('tr');
    var addCell = document.createElement('td');
    addCell.colSpan = emptyRow.children.length;
    var addLink = document.createElement('a');
    addLink.href = 'javascript:void(0)';
    addLink.className = 'add-row';
    addLink.textContent = options.addText;
    addCell.appendChild(addLink);
    addRow.appendChild(addCell);
    tbody.appendChild(addRow);

    addLink.addEventListener('click', function () {
        var formCount = parseInt(totalForms.value, 10);
        var newRow = emptyRow.cloneNode(true);
        newRow.classList.remove('hidden', 'empty-form');
        newRow.querySelectorAll('[name], [id]').forEach(function (el) {
            if (el.name) {
                el.name = el.name.replace('__prefix__', formCount);
            }
            if (el.id) {
                el.id = el.id.replace('__prefix__', formCount);
            }
        });
        newRow.querySelectorAll('label[for]').forEach(function (label) {
            label.setAttribute('for', label.getAttribute('for').replace('__prefix__', formCount));
        });
        tbody.insertBefore(newRow, addRow);
        replaceAttachmentDeleteCheckbox(newRow, options.deleteText);
        totalForms.value = formCount + 1;
    });
}
