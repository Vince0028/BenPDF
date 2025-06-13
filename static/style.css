<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Universal File & Base Converter</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen p-4">

    <div class="message-box" id="messageBox">
        <p id="messageText"></p>
        <button onclick="hideMessageBox()">OK</button>
    </div>

    <div class="loading-overlay" id="loadingOverlay">
        <div class="spinner"></div>
    </div>

    <div class="container">
        <!-- Image Converter Section -->
        <div class="section flex flex-col gap-4">
            <h2 class="text-2xl font-bold text-gray-800 text-center">Image Converter</h2>
            <div class="file-input-group">
                <label for="imageFileInput" class="text-gray-700 font-medium">Upload Image (PNG, JPG, GIF, WEBP)</label>
                <input type="file" id="imageFileInput" accept=".png,.jpg,.jpeg,.gif,.webp" class="input-field file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer">
            </div>
            <div class="text-center text-gray-500 my-2">OR</div>
            <div class="file-input-group">
                <label for="imageUrlInput" class="text-gray-700 font-medium">Image URL</label>
                <input type="url" id="imageUrlInput" placeholder="e.g., https://example.com/image.jpg" class="input-field">
            </div>
            <button onclick="convertImage()" class="btn"><span>Convert Image to PNG</span></button>
        </div>

        <!-- Document Converter Section -->
        <div class="section flex flex-col gap-4">
            <h2 class="text-2xl font-bold text-gray-800 text-center">Document Converter</h2>
            <div class="file-input-group">
                <label for="documentFileInput" class="text-gray-700 font-medium">Upload Document (PDF, DOC, DOCX)</label>
                <input type="file" id="documentFileInput" accept=".pdf,.doc,.docx" class="input-field file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer">
            </div>
            <button onclick="convertDocument()" class="btn"><span>Convert Document</span></button>
        </div>

        <!-- Binary / Base Converter Section -->
        <div class="section flex flex-col gap-4">
            <h2 class="text-2xl font-bold text-gray-800 text-center">Base Converter</h2>
            <div class="base-input-group">
                <label for="baseInputValue" class="text-gray-700 font-medium">Number to Convert</label>
                <input type="text" id="baseInputValue" placeholder="Enter number" class="input-field">
            </div>
            <div class="base-input-group">
                <label for="sourceBaseSelect" class="text-gray-700 font-medium">Source Base</label>
                <select id="sourceBaseSelect" class="input-field">
                    <option value="binary">Binary (Base 2)</option>
                    <option value="decimal" selected>Decimal (Base 10)</option>
                    <option value="octal">Octal (Base 8)</option>
                    <option value="hexadecimal">Hexadecimal (Base 16)</option>
                </select>
            </div>
            <div class="base-input-group">
                <label for="targetBaseSelect" class="text-gray-700 font-medium">Target Base</label>
                <select id="targetBaseSelect" class="input-field">
                    <option value="binary">Binary (Base 2)</option>
                    <option value="decimal">Decimal (Base 10)</option>
                    <option value="octal">Octal (Base 8)</option>
                    <option value="hexadecimal" selected>Hexadecimal (Base 16)</option>
                </select>
            </div>
            <button onclick="convertBase()" class="btn"><span>Convert Base</span></button>
            <div class="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-md">
                <p class="text-sm font-medium text-gray-600">Converted Result:</p>
                <p id="baseConversionResult" class="text-lg font-bold text-blue-700 break-words"></p>
                <p class="text-sm font-medium text-gray-600 mt-4">Solution Steps:</p>
                <pre id="baseConversionSolution" class="text-sm text-gray-800 whitespace-pre-wrap font-mono"></pre>
            </div>
        </div>
    </div>

    <script src="{{ url_for('static', filename='script.js') }}"></script>
</body>
</html>
