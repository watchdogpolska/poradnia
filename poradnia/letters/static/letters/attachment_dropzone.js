document.addEventListener('DOMContentLoaded', function () {
    var dropZone = document.getElementById('drop-zone');
    var clearButton = document.getElementById('clear-files-button');
    var fileInput = document.getElementById('id_file_field');
    if (!dropZone || !fileInput) {
        return;
    }
    var selectedFilesList = new DataTransfer();

    // Highlight drop zone when drag event occurs
    dropZone.addEventListener('dragover', function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.style.backgroundColor = 'lightgray';
    });
    dropZone.addEventListener('dragleave', function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.style.backgroundColor = '#f5f5f5';
    });
    // Handle the drop event
    dropZone.addEventListener('drop', function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.style.backgroundColor = '#f5f5f5';
        handleNewFiles(e.dataTransfer.files);
        clearButton.style.display = 'inline-block';
    });
    // Attach an event listener to the file input change event
    fileInput.addEventListener('change', function (e) {
        handleNewFiles(e.target.files);
        clearButton.style.display = selectedFilesList.files.length > 0 ? 'inline-block' : 'none';
    });
    // Use a button to clear files
    clearButton.addEventListener('click', function () {
        fileInput.files = new DataTransfer().files;
        selectedFilesList = new DataTransfer();
        updateTableWithFiles([]);
        clearButton.style.display = 'none';
    });

    var filesTableHead = document.getElementById('files-table-head');
    if (filesTableHead) {
        var labelHeight = filesTableHead.offsetHeight;
        document.querySelectorAll('.control-label').forEach(function (el) {
            el.style.height = (labelHeight - 5) + 'px';
        });
    }

    // Function to update the table with files
    function updateTableWithFiles(files) {
        var tableBody = document.querySelector('#selected-files tbody');
        if (!tableBody) {
            return;
        }
        tableBody.innerHTML = '';
        for (var i = 0; i < files.length; i++) {
            var row = document.createElement('tr');
            row.className = 'dynamic-form';
            var cell = document.createElement('td');
            cell.textContent = files[i].name;
            row.appendChild(cell);
            tableBody.appendChild(row);
        }
    }

    function handleNewFiles(eventFiles) {
        var addedFiles = Array.from(eventFiles);
        var selectedFiles = Array.from(selectedFilesList.files);
        var newFiles = addedFiles.filter(function (addedFile) {
            return !selectedFiles.some(function (selectedFile) {
                return selectedFile.name === addedFile.name &&
                    selectedFile.size === addedFile.size &&
                    selectedFile.lastModified === addedFile.lastModified;
            });
        });
        newFiles.forEach(function (file) {
            selectedFilesList.items.add(file);
        });

        updateTableWithFiles(selectedFilesList.files);
        fileInput.files = selectedFilesList.files;
    }
});
