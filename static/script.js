function showMessageBox(message) {
    document.getElementById('messageText').innerText = message;
    document.getElementById('messageBox').style.display = 'block';
}

function hideMessageBox() {
    document.getElementById('messageBox').style.display = 'none';
}

function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

// Function to handle Image Conversion (from file upload or URL)
async function convertImage() {
    const imageFileInput = document.getElementById('imageFileInput');
    const imageUrlInput = document.getElementById('imageUrlInput');
    const formData = new FormData();

    if (imageFileInput.files.length > 0) {
        formData.append('file', imageFileInput.files[0]);
    } else if (imageUrlInput.value.trim() !== '') {
        formData.append('url', imageUrlInput.value.trim());
    } else {
        showMessageBox('Please upload an image file or provide an image URL.');
        return;
    }

    showLoading();
    try {
        const response = await fetch('/api/convert-image', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            // Extract filename from Content-Disposition header, or use a default
            const contentDisposition = response.headers.get('Content-Disposition');
            a.download = contentDisposition ? contentDisposition.split('filename=')[1].trim().replace(/"/g, '') : 'converted_image.png';
            
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            showMessageBox('Image converted and download initiated!');
        } else {
            const errorData = await response.json();
            showMessageBox(`Error: ${errorData.error || response.statusText}`);
        }
    } catch (error) {
        console.error('Error:', error);
        showMessageBox('An unexpected error occurred during image conversion.');
    } finally {
        hideLoading();
        // Clear input fields
        imageFileInput.value = '';
        imageUrlInput.value = '';
    }
}

// Function to handle Document Conversion (PDF <-> DOCX)
async function convertDocument() {
    const documentFileInput = document.getElementById('documentFileInput');
    if (documentFileInput.files.length === 0) {
        showMessageBox('Please upload a document file (PDF, DOC, DOCX).');
        return;
    }

    const formData = new FormData();
    formData.append('file', documentFileInput.files[0]);

    showLoading();
    try {
        const response = await fetch('/api/convert-document', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            // Extract filename from Content-Disposition header, or use a default
            const contentDisposition = response.headers.get('Content-Disposition');
            a.download = contentDisposition ? contentDisposition.split('filename=')[1].trim().replace(/"/g, '') : 'converted_document.pdf';
            
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            showMessageBox('Document converted and download initiated!');
        } else {
            const errorData = await response.json();
            showMessageBox(`Error: ${errorData.error || response.statusText}`);
        }
    } catch (error) {
        console.error('Error:', error);
        showMessageBox('An unexpected error occurred during document conversion.');
    } finally {
        hideLoading();
        documentFileInput.value = ''; // Clear input field
    }
}

// Function to handle Base Conversion (Binary, Decimal, Octal, Hexadecimal)
async function convertBase() {
    const inputValue = document.getElementById('baseInputValue').value.trim();
    const sourceBase = document.getElementById('sourceBaseSelect').value;
    const targetBase = document.getElementById('targetBaseSelect').value;
    const resultDisplay = document.getElementById('baseConversionResult');
    const solutionDisplay = document.getElementById('baseConversionSolution');

    resultDisplay.innerText = ''; // Clear previous results
    solutionDisplay.innerText = ''; // Clear previous solution

    if (!inputValue) {
        showMessageBox('Please enter a number to convert.');
        return;
    }

    showLoading();
    try {
        const response = await fetch('/api/convert-base', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                inputValue: inputValue,
                sourceBase: sourceBase,
                targetBase: targetBase
            }),
        });

        if (response.ok) {
            const data = await response.json();
            if (data.result) {
                resultDisplay.innerText = data.result;
                solutionDisplay.innerText = data.solution;
                showMessageBox('Base conversion successful!');
            } else {
                resultDisplay.innerText = 'Error: No result.';
                showMessageBox('Error: No result from conversion.');
            }
        } else {
            const errorData = await response.json();
            resultDisplay.innerText = `Error: ${errorData.error || response.statusText}`;
            showMessageBox(`Error: ${errorData.error || response.statusText}`);
        }
    } catch (error) {
        console.error('Error:', error);
        resultDisplay.innerText = 'An unexpected error occurred.';
        showMessageBox('An unexpected error occurred during base conversion.');
    } finally {
        hideLoading();
    }
}
