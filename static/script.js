// --- Helper Function for Messages ---
function showMessage(elementId, text, type) {
    const messageElement = document.getElementById(elementId);
    messageElement.textContent = text;
    messageElement.className = `message ${type}`;
    messageElement.style.display = 'block';
    setTimeout(() => {
        messageElement.style.display = 'none';
        messageElement.textContent = '';
        messageElement.className = 'message'; // Reset class
    }, 7000); // Hide after 7 seconds
}

// --- Event Listeners for File Inputs and URL Input ---
document.addEventListener('DOMContentLoaded', () => {
    const imageUploadInput = document.getElementById('imageUpload');
    const imageFileNameDisplay = document.getElementById('imageFileNameDisplay');
    const imageUploadLabel = document.getElementById('imageUploadLabel');
    const screenshotUrlInput = document.getElementById('screenshotUrl');

    imageUploadInput.addEventListener('change', () => {
        if (imageUploadInput.files.length > 0) {
            imageFileNameDisplay.textContent = `Selected: ${imageUploadInput.files[0].name}`;
            imageUploadLabel.textContent = 'Change File';
            screenshotUrlInput.value = ''; // Clear URL if file is chosen
        } else {
            imageFileNameDisplay.textContent = 'No file chosen';
            imageUploadLabel.textContent = 'Choose File';
        }
        document.getElementById('imagePreview').style.display = 'none';
        showMessage('imageMessage', '', ''); // Clear previous messages
    });

    screenshotUrlInput.addEventListener('input', () => {
        imageUploadInput.value = ''; // Clear file input if URL is typed
        imageFileNameDisplay.textContent = 'No file chosen';
        imageUploadLabel.textContent = 'Choose File';
        document.getElementById('imagePreview').style.display = 'none';
        showMessage('imageMessage', '', ''); // Clear previous messages
    });


    const documentFileInput = document.getElementById('documentFile');
    const documentFileNameDisplay = document.getElementById('documentFileNameDisplay');
    const documentUploadLabel = document.getElementById('documentUploadLabel');

    documentFileInput.addEventListener('change', () => {
        if (documentFileInput.files.length > 0) {
            documentFileNameDisplay.textContent = `Selected: ${documentFileInput.files[0].name}`;
            documentUploadLabel.textContent = 'Change File';
        } else {
            documentFileNameDisplay.textContent = 'No file chosen';
            documentUploadLabel.textContent = 'Choose File';
        }
        showMessage('documentMessage', '', ''); // Clear previous messages
    });
});

// --- Conversion Functions (Now communicating with Flask Backend) ---

async function convertScreenshotOrImage() {
    const urlInput = document.getElementById('screenshotUrl');
    const imageUploadInput = document.getElementById('imageUpload');
    const imgPreview = document.getElementById('imagePreview');
    const messageId = 'imageMessage';

    let fileToSend = null;

    // Priority: File upload then URL
    if (imageUploadInput.files.length > 0) {
        fileToSend = imageUploadInput.files[0];
    } else if (urlInput.value.trim()) {
        const imageUrl = urlInput.value.trim();
        try {
            new URL(imageUrl); // Basic validation
        } catch (e) {
            showMessage(messageId, 'Please enter a valid URL.', 'error');
            return;
        }
        // Fetch the image from the URL to send it as a Blob
        showMessage(messageId, 'Fetching image from URL...', 'info');
        try {
            // Ensure CORS is handled on the server serving the image if it's cross-origin
            const response = await fetch(imageUrl, {mode: 'cors'});
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const blob = await response.blob();
            // Create a File object from Blob, Flask expects a File-like object
            fileToSend = new File([blob], 'remote_image.jpg', { type: blob.type });
        } catch (error) {
            showMessage(messageId, `Failed to fetch image from URL: ${error.message}. Please ensure the URL is correct and the image server allows CORS.`, 'error');
            return;
        }
    } else {
        showMessage(messageId, 'Please upload an image file OR paste an image URL.', 'error');
        return;
    }

    // Show loading message
    showMessage(messageId, 'Converting image...', 'info');
    imgPreview.style.display = 'none'; // Hide preview during conversion

    const formData = new FormData();
    formData.append('file', fileToSend); // Key 'file' must match what Flask expects

    try {
        const response = await fetch('/api/convert-image', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const blob = await response.blob(); // Get the response as a Blob
            const downloadUrl = URL.createObjectURL(blob); // Create a temporary URL for the Blob

            // Extract filename from Content-Disposition header
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'converted_image.jpg'; // Default if header is missing
            if (contentDisposition && contentDisposition.includes('filename=')) {
                filename = contentDisposition.split('filename=')[1].trim().replace(/"/g, '');
            }

            // Display preview for the new Blob (if it's an image)
            if (blob.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imgPreview.src = e.target.result;
                    imgPreview.style.display = 'block';
                };
                reader.readAsDataURL(blob);
            } else {
                imgPreview.style.display = 'none';
            }

            // Trigger the download
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename; // Set the download filename
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(downloadUrl); // Clean up the Blob URL

            showMessage(messageId, `Image converted and downloaded as "${filename}".`, 'success');
            // Clear inputs
            urlInput.value = '';
            imageUploadInput.value = '';
            document.getElementById('imageFileNameDisplay').textContent = 'No file chosen';
            document.getElementById('imageUploadLabel').textContent = 'Choose File';

        } else {
            // If response is not OK, try to parse JSON error message
            const errorData = await response.json();
            showMessage(messageId, `Conversion failed: ${errorData.error || response.statusText}`, 'error');
        }
    } catch (error) {
        showMessage(messageId, `An error occurred: ${error.message}`, 'error');
        console.error('Fetch error:', error);
    }
}

async function convertDocumentFile() {
    const documentFileInput = document.getElementById('documentFile');
    const messageId = 'documentMessage';

    if (documentFileInput.files.length === 0) {
        showMessage(messageId, 'Please upload a document file.', 'error');
        return;
    }

    const fileToConvert = documentFileInput.files[0];
    showMessage(messageId, 'Converting document...', 'info');

    const formData = new FormData();
    formData.append('file', fileToConvert); // Key 'file' must match what Flask expects

    try {
        const response = await fetch('/api/convert-document', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const blob = await response.blob(); // Get the response as a Blob
            const downloadUrl = URL.createObjectURL(blob); // Create a temporary URL for the Blob

            // Extract filename from Content-Disposition header
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'converted_document.pdf'; // Default if header is missing
            if (contentDisposition && contentDisposition.includes('filename=')) {
                filename = contentDisposition.split('filename=')[1].trim().replace(/"/g, '');
            }

            // Trigger the download
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename; // Set the download filename
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(downloadUrl); // Clean up the Blob URL

            showMessage(messageId, `Document converted and downloaded as "${filename}".`, 'success');
            // Clear inputs
            documentFileInput.value = '';
            document.getElementById('documentFileNameDisplay').textContent = 'No file chosen';
            document.getElementById('documentUploadLabel').textContent = 'Choose File';

        } else {
            // If response is not OK, try to parse JSON error message
            const errorData = await response.json();
            showMessage(messageId, `Conversion failed: ${errorData.error || response.statusText}`, 'error');
        }
    } catch (error) {
        showMessage(messageId, `An error occurred: ${error.message}`, 'error');
        console.error('Fetch error:', error);
    }
}