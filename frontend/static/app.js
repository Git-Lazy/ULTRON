const API_BASE = 'http://localhost:8000';

const state = {
    premadeClasses: [],
    customClasses: [],
    selectedClass: null,
    pendingCustomExamples: [],
};

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
            renderCustomClassExamples();
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
        const res = await fetch(`${API_BASE}/api-key`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const key = data && data.api_key ? ` · API key (CHANGE MSG BEFORE USE): ${data.api_key}` : '';
        setStatus(`Connected${key}`);
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
    renderCustomClassExamples();
}

function readFileAsDataURL(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

async function handleImageUpload(event) {
    const target = document.getElementById('uploaded-images');
    const file = (event.target && event.target.files && event.target.files[0]) || (event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0]);
    if (!file) return;

    const img = document.createElement('img');
    img.src = URL.createObjectURL(file);
    img.className = 'thumb';
    img.alt = file.name;
    target.appendChild(img);

    setStatus('Uploading...');
    try {
        const form = new FormData();
        form.append('image', file, file.name);
        if (state.selectedClass) form.append('class', state.selectedClass);
        const res = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: form
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setStatus('System online');
    } catch (err) {
        console.error(err);
        setStatus('Backend offline (image upload issue: change)', false);
    }
    if (event.target && 'value' in event.target) event.target.value = '';
}

async function handleFolderUpload(event) {
    const grid = document.getElementById('uploaded-folder-images');
    const summary = document.getElementById('folder-summary');
    grid.innerHTML = '';

    const files = Array.from(event.target.files).filter(f => f.type.startsWith('image/'));
    if (files.length === 0) {
        summary.textContent = 'No images found';
        return;
    }

    const folderName = files[0].webkitRelativePath.split('/')[0] || 'folder';
    summary.textContent = `${folderName} · ${files.length} images`;

    for (const file of files.slice(0, 24)) {
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.className = 'thumb';
        img.alt = file.name;
        grid.appendChild(img);
    }

    setStatus('Uploading folder...');
    try {
        const form = new FormData();
        form.append('folder', folderName);
        for (const file of files) {
            form.append('images', file, file.webkitRelativePath || file.name);
        }
        const res = await fetch(`${API_BASE}/api/upload-folder`, {
            method: 'POST',
            body: form
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setStatus('System online');
    } catch (err) {
        console.error(err);
        setStatus('Backend offline (folder upload issue: change)', false);
    }
    event.target.value = '';
}

async function handleSearch() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;
    setStatus('Querying...');
    try {
        const res = await fetch(`${API_BASE}/api/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        renderOutput(data.images);
        setStatus('System online');
    } catch (err) {
        console.error(err);
        setStatus('Backend offline (search issue: change)', false);
    }
}

renderClassList();
pingBackend();
loadPremadeClasses().then(loadSavedExamples);