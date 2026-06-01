const API_BASE = 'http://localhost:8000';

const state = {
    premadeClasses: [],
    customClasses: [],
    selectedClass: null,
    pendingCustomExamples: [],
    // Deferred selections: real absolute paths held until the user clicks
    // "Send", so a mis-click can be changed before anything reaches the backend.
    classifyPath: null,
    folderPath: null,
};

// pywebview exposes Python under window.pywebview.api. When absent (plain
// browser / Docker headless) we fall back to the hidden <input type=file>,
// which only yields a sandboxed file name rather than a real path.
function hasNativePicker() {
    return !!(window.pywebview && window.pywebview.api && window.pywebview.api.pick_image);
}

// Text renderer for prediction results (renderOutput is for image URLs).
function renderPredictions(lines) {
    const target = document.getElementById('output-images');
    target.innerHTML = '';
    if (!lines || lines.length === 0) {
        const ph = document.createElement('div');
        ph.className = 'image-placeholder';
        ph.textContent = 'No results';
        target.appendChild(ph);
        return;
    }
    for (const line of lines) {
        const row = document.createElement('div');
        row.className = 'prediction-result';
        row.textContent = line;
        target.appendChild(row);
    }
}

function setStatus(text, ok = true) {
    const dot = document.querySelector('.status-dot');
    document.querySelector('.status-text').textContent = text;
    dot.style.background = ok ? '#4ade80' : '#c8102e';
    dot.style.boxShadow = `0 0 8px ${ok ? '#4ade80' : '#c8102e'}`;
}

function renderOutput(images) {
    const target = document.getElementById('output-images');
    target.innerHTML = '';
    if (!images || images.length === 0) {
        const ph = document.createElement('div');
        ph.className = 'image-placeholder';
        ph.textContent = 'No results';
        target.appendChild(ph);
        return;
    }
    for (const src of images) {
        const img = document.createElement('img');
        img.src = src;
        img.className = 'thumb';
        target.appendChild(img);
    }
}

function renderClassList() {
    const list = document.getElementById('class-list');
    const empty = document.getElementById('class-empty');
    const addBtn = document.getElementById('add-custom-class');

    list.querySelectorAll('.class-chip:not(.class-chip--custom)').forEach(el => el.remove());

    const all = [
        ...state.premadeClasses.map(c => ({ name: c, custom: false })),
        ...state.customClasses.map(c => ({ name: c.name, custom: true })),
    ];

    empty.style.display = all.length === 0 ? '' : 'none';

    for (const cls of all) {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'class-chip';
        if (cls.custom) chip.classList.add('class-chip--user');
        if (state.selectedClass === cls.name) chip.classList.add('class-chip--selected');
        chip.textContent = cls.name;
        chip.onclick = () => {
            state.selectedClass = state.selectedClass === cls.name ? null : cls.name;
            renderClassList();
            renderCustomClassExamplesShowHide();
        };
        list.insertBefore(chip, addBtn);
    }
}

function renderCustomClassExamples() {
    const displayDiv = document.getElementById('custom-class-examples-display');
    const grid = document.getElementById('custom-class-examples-grid');
    const nameLabel = document.getElementById('selected-class-name');

    grid.innerHTML = '';

    if (!state.selectedClass) {
        displayDiv.hidden = true;
        return;
    }

    const customClass = state.customClasses.find(c => c.name === state.selectedClass);

    if (!customClass || !customClass.examplePaths || customClass.examplePaths.length === 0) {
        displayDiv.hidden = true;
        return;
    }

    displayDiv.hidden = false;
    if (nameLabel) nameLabel.textContent = customClass.name;

    for (const filePath of customClass.examplePaths) {
        const img = document.createElement('img');
        const filename = filePath.split(/[\\/]/).pop();
        img.src = `${API_BASE}/api/examples/${encodeURIComponent(customClass.name)}/${encodeURIComponent(filename)}`;
        img.className = 'thumb';
        img.alt = filename;
        img.onerror = () => { img.alt = `Failed to load ${filename}`; };
        grid.appendChild(img);
    }
}

function showCustomClassError(message) {
    const errorDiv = document.getElementById('custom-class-error');
    if (!errorDiv) return;
    if (!message) {
        errorDiv.hidden = true;
        errorDiv.textContent = '';
        return;
    }
    errorDiv.textContent = message;
    errorDiv.hidden = false;
}

async function pingBackend() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setStatus('Connected');
    } catch (err) {
        console.error(err);
        setStatus('Backend unreachable', false);
    }
}

async function loadPremadeClasses() {
    try {
        const res = await fetch(`${API_BASE}/api/classes`);
        if (!res.ok) return;
        const data = await res.json();
        if (Array.isArray(data.classes)) {
            state.premadeClasses = data.classes;
            renderClassList();
        }
    } catch (_) {
        // Backend not reachable yet; leave the slot empty.
    }
}

async function loadSavedExamples() {
    try {
        const res = await fetch(`${API_BASE}/api/examples`);
        if (!res.ok) return;
        const data = await res.json();
        const examples = data.examples || {};
        for (const [className, paths] of Object.entries(examples)) {
            // register class name but don't assume backend serves images
            let entry = state.customClasses.find(c => c.name === className);
            if (!entry) {
                entry = { name: className, examples: [], examplePaths: [] };
                state.customClasses.push(entry);
            }
            // Keep premadeClasses and customClasses separate
            state.premadeClasses = state.premadeClasses.filter(n => n !== className);
        }
        renderClassList();
    } catch (_) {
        // Backend not reachable yet.
    }
}

function toggleCustomClassForm() {
    const form = document.getElementById('custom-class-form');
    form.hidden = !form.hidden;
    if (form.hidden) cancelCustomClass();
}

function handleCustomClassExamples(event) {
    const grid = document.getElementById('custom-class-images');
    const files = Array.from(event.target.files);
    for (const file of files) {
        state.pendingCustomExamples.push(file);
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.className = 'thumb';
        img.alt = file.name;
        grid.appendChild(img);
    }
    if (state.pendingCustomExamples.length > 0) showCustomClassError(null);
    event.target.value = '';
}

function cancelCustomClass() {
    document.getElementById('custom-class-name').value = '';
    document.getElementById('custom-class-images').innerHTML = '';
    state.pendingCustomExamples = [];
    document.getElementById('custom-class-form').hidden = true;
    showCustomClassError(null);
}

async function saveCustomClass() {
    const nameInput = document.getElementById('custom-class-name');
    const name = nameInput.value.trim();
    const examples = state.pendingCustomExamples.slice();

    if (!name && examples.length === 0) {
        showCustomClassError('A class name and at least one example image are required.');
        nameInput.focus();
        return;
    }
    if (!name) {
        showCustomClassError('A class name is required.');
        nameInput.focus();
        return;
    }
    if (examples.length === 0) {
        showCustomClassError('At least one example image is required.');
        document.getElementById('custom-class-examples').focus();
        return;
    }
    showCustomClassError(null);

    // Convert example files to data URLs for local display
    const dataUrls = await Promise.all(examples.map(f => readFileAsDataURL(f)));

    const customEntry = { name, examples: dataUrls, examplePaths: [] };
    state.customClasses.push(customEntry);
    state.selectedClass = name;

    setStatus('Saving class...');
    try {
        // Inform backend about new class (no files)
        const res = await fetch(`${API_BASE}/api/classes?class_name=${encodeURIComponent(name)}`, {
            method: 'POST'
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setStatus('System online');
    } catch (err) {
        console.error(err);
        setStatus('Backend offline (class saving issue: change)', false);
    }

    cancelCustomClass();
    renderClassList();
    renderCustomClassExamplesShowHide();
}

function readFileAsDataURL(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// Show a single preview thumbnail and arm the Send button for the chosen image.
function setClassifyPreview(src, path, label) {
    const target = document.getElementById('uploaded-images');
    target.innerHTML = '';
    const img = document.createElement('img');
    img.src = src;
    img.className = 'thumb';
    img.alt = label || path;
    target.appendChild(img);

    state.classifyPath = path;
    const sendBtn = document.getElementById('classify-send');
    if (sendBtn) sendBtn.disabled = false;
}

// Drop-zone click: native dialog gives a real path; browser fallback uses the input.
async function pickClassifyImage() {
    if (!hasNativePicker()) {
        document.getElementById('upload-input').click();
        return;
    }
    try {
        const picked = await window.pywebview.api.pick_image();
        if (!picked) return;
        setClassifyPreview(picked.data_url, picked.path, picked.path.split(/[\\/]/).pop());
    } catch (err) {
        console.error(err);
        setStatus('Could not open file dialog', false);
    }
}

// Browser fallback only: the File gives a blob preview but just a bare name as "path".
function handleImageUpload(event) {
    const file = (event.target && event.target.files && event.target.files[0]) || (event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0]);
    if (!file) return;
    setClassifyPreview(URL.createObjectURL(file), file.name, file.name);
    if (event.target && 'value' in event.target) event.target.value = '';
}

async function sendClassifyImage() {
    const imagePath = state.classifyPath;
    if (!imagePath) return;

    const sendBtn = document.getElementById('classify-send');
    if (sendBtn) sendBtn.disabled = true;
    setStatus('Classifying...');
    try {
        // get_prediction_from_model expects the image *path*, not the bytes.
        const res = await fetch(`${API_BASE}/api/predict-image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image_path: imagePath })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const name = data.class_name || 'No matching class';
        renderPredictions([`${imagePath.split(/[\\/]/).pop()} → ${name}`]);
        setStatus('System online');
    } catch (err) {
        console.error(err);
        setStatus('Backend offline (classify issue: change)', false);
    } finally {
        if (sendBtn) sendBtn.disabled = false;
    }
}

function setFolderSelection(path) {
    state.folderPath = path;
    document.getElementById('folder-summary').textContent = path;
    const sendBtn = document.getElementById('folder-send');
    if (sendBtn) sendBtn.disabled = false;
}

// Drop-zone click: native dialog returns a real folder path; browser falls back to the input.
async function pickFolder() {
    if (!(window.pywebview && window.pywebview.api && window.pywebview.api.pick_folder)) {
        document.getElementById('folder-input').click();
        return;
    }
    try {
        const picked = await window.pywebview.api.pick_folder();
        if (!picked) return;
        document.getElementById('uploaded-folder-images').innerHTML = '';
        setFolderSelection(picked.path);
    } catch (err) {
        console.error(err);
        setStatus('Could not open folder dialog', false);
    }
}

// Browser fallback only: shows thumbnails but can only report the top folder name.
function handleFolderUpload(event) {
    const grid = document.getElementById('uploaded-folder-images');
    grid.innerHTML = '';

    const files = Array.from(event.target.files).filter(f => f.type.startsWith('image/'));
    if (files.length === 0) {
        document.getElementById('folder-summary').textContent = 'No images found';
        state.folderPath = null;
        const sendBtn = document.getElementById('folder-send');
        if (sendBtn) sendBtn.disabled = true;
        return;
    }

    const folderName = files[0].webkitRelativePath.split('/')[0] || 'folder';
    for (const file of files.slice(0, 24)) {
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.className = 'thumb';
        img.alt = file.name;
        grid.appendChild(img);
    }
    setFolderSelection(folderName);
    event.target.value = '';
}

async function sendFolder() {
    const folderPath = state.folderPath;
    if (!folderPath) return;

    const sendBtn = document.getElementById('folder-send');
    if (sendBtn) sendBtn.disabled = true;
    setStatus('Sorting folder...');
    try {
        // Backend exposes POST /sort?folder_path=... (folder_path is a query
        // param), which starts sorting and returns {status} rather than the
        // per-file {results} the original /api/predict-folder contract promised.
        const res = await fetch(`${API_BASE}/sort?folder_path=${encodeURIComponent(folderPath)}`, {
            method: 'POST'
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        renderPredictions([`${folderPath} → ${data.status || 'sorting started'}`]);
        setStatus('System online');
    } catch (err) {
        console.error(err);
        setStatus('Backend offline (folder sort issue: change)', false);
    } finally {
        if (sendBtn) sendBtn.disabled = false;
    }
}

async function handleSearch() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;
    setStatus('Querying...');
    try {
        // Backend exposes GET /api/search?query=... returning {results: [paths]}
        // (the POST /api/query {images} endpoint this UI was written for does
        // not exist). Paths are server-side file paths, so the thumbnails will
        // only resolve once the backend serves those images over HTTP.
        const res = await fetch(`${API_BASE}/api/search?query=${encodeURIComponent(query)}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        renderOutput(data.results);
        setStatus('System online');
    } catch (err) {
        console.error(err);
        setStatus('Backend offline (search issue: change)', false);
    }
}

// Renderer that uses show/hide behavior and prefers local data-URLs for user-created classes
function renderCustomClassExamplesShowHide() {
    const displayDiv = document.getElementById('custom-class-examples-display');
    const grid = document.getElementById('custom-class-examples-grid');
    const nameLabel = document.getElementById('selected-class-name');

    grid.innerHTML = '';

    if (!state.selectedClass) {
        displayDiv.hidden = true;
        return;
    }

    const customClass = state.customClasses.find(c => c.name === state.selectedClass);

    // If we have local data-URL examples for this custom class, show them and return
    if (customClass && Array.isArray(customClass.examples) && customClass.examples.length > 0) {
        displayDiv.hidden = false;
        if (nameLabel) nameLabel.textContent = customClass.name;
        for (const dataUrl of customClass.examples) {
            const img = document.createElement('img');
            img.src = dataUrl;
            img.className = 'thumb';
            img.alt = customClass.name;
            grid.appendChild(img);
        }
        return;
    }

    // Otherwise fall back to server-side examplePaths (if present)
    if (!customClass || !customClass.examplePaths || customClass.examplePaths.length === 0) {
        displayDiv.hidden = true;
        return;
    }

    displayDiv.hidden = false;
    if (nameLabel) nameLabel.textContent = customClass.name;

    for (const filePath of customClass.examplePaths) {
        const img = document.createElement('img');
        const filename = filePath.split(/[\\\\/]/).pop();
        img.src = `${API_BASE}/api/examples/${encodeURIComponent(customClass.name)}/${encodeURIComponent(filename)}`;
        img.className = 'thumb';
        img.alt = filename;
        img.onerror = () => { img.alt = `Failed to load ${filename}`; };
        grid.appendChild(img);
    }
}

renderClassList();
pingBackend();
loadPremadeClasses().then(loadSavedExamples);