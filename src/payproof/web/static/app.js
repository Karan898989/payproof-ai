// PayProof AI Client Interactions

function switchRole(role) {
    document.cookie = `payproof_user=${role}; path=/; max-age=31536000; SameSite=Lax`;
    window.location.reload();
}

function openNewCaseModal() {
    document.getElementById('new-case-modal').classList.remove('hidden');
}

function closeNewCaseModal() {
    document.getElementById('new-case-modal').classList.add('hidden');
}

function openSettingsModal() {
    document.getElementById('settings-modal').classList.remove('hidden');
    loadSettingsStatus();
}

function closeSettingsModal() {
    document.getElementById('settings-modal').classList.add('hidden');
}

async function loadSettingsStatus() {
    try {
        const res = await fetch('/api/v1/settings/status');
        const data = await res.json();
        const statusEl = document.getElementById('modal-nim-status');
        if (data.nim_configured) {
            statusEl.innerHTML = `<span class="text-emerald-700 font-bold flex items-center"><i data-lucide="check-circle" class="w-3.5 h-3.5 mr-1"></i> Configured: ${data.masked_api_key}</span> Model: ${data.model}`;
            document.getElementById('nim-badge-dot').className = 'w-2 h-2 rounded-full bg-emerald-500 ml-1';
        } else {
            statusEl.innerHTML = `<span class="text-amber-600 font-bold flex items-center"><i data-lucide="alert-circle" class="w-3.5 h-3.5 mr-1"></i> No API key configured</span> System running in pure deterministic fallback mode.`;
            document.getElementById('nim-badge-dot').className = 'w-2 h-2 rounded-full bg-amber-400 ml-1';
        }
        if (window.lucide) lucide.createIcons();
    } catch (e) {
        console.error("Failed to load settings status", e);
    }
}

async function saveApiKey() {
    const key = document.getElementById('modal-api-key').value.trim();
    if (!key) {
        alert("Please enter a valid NVIDIA API Key.");
        return;
    }
    try {
        const res = await fetch('/api/v1/settings/update-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nvidia_api_key: key })
        });
        const data = await res.json();
        alert(data.message || "Key saved.");
        document.getElementById('modal-api-key').value = '';
        loadSettingsStatus();
    } catch (e) {
        alert("Failed to save key: " + e.message);
    }
}

async function testNimConnection() {
    const statusEl = document.getElementById('modal-nim-status');
    statusEl.innerText = "Pinging NVIDIA NIM API endpoint...";
    try {
        const res = await fetch('/api/v1/settings/test-nim', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            statusEl.innerHTML = `<span class="text-emerald-700 font-bold">✓ ${data.message}</span>`;
        } else {
            statusEl.innerHTML = `<span class="text-red-600 font-bold">✗ ${data.message}</span>`;
        }
    } catch (e) {
        statusEl.innerHTML = `<span class="text-red-600 font-bold">✗ Error: ${e.message}</span>`;
    }
}

async function handleCreateCase(e) {
    e.preventDefault();
    const caseNumber = document.getElementById('new-case-number').value.trim();
    const vendorId = document.getElementById('new-vendor-id').value.trim() || null;
    const vendorName = document.getElementById('new-vendor-name').value.trim() || null;
    const amount = parseFloat(document.getElementById('new-amount').value) || 0.0;
    const currency = document.getElementById('new-currency').value;
    const invoiceRef = document.getElementById('new-invoice-ref').value.trim() || null;

    try {
        const res = await fetch('/api/v1/cases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                case_number: caseNumber,
                vendor_id: vendorId,
                vendor_name: vendorName,
                amount: amount,
                currency: currency,
                invoice_reference: invoiceRef
            })
        });

        if (!res.ok) {
            const err = await res.json();
            alert("Error: " + (err.detail || "Failed to create case"));
            return;
        }

        const data = await res.json();
        window.location.href = `/cases/${data.id}`;
    } catch (err) {
        alert("Failed to create case: " + err.message);
    }
}

async function runVerification() {
    const container = document.getElementById('case-container');
    if (!container) return;
    const caseId = container.dataset.caseId;
    const btn = document.getElementById('btn-run-analysis');
    btn.disabled = true;
    btn.innerHTML = `<span class="inline-block animate-spin mr-2">⚙</span> Analyzing with Rules & Nemotron...`;

    try {
        const res = await fetch(`/api/v1/cases/${caseId}/analyze`, { method: 'POST' });
        if (!res.ok) {
            const err = await res.json();
            alert("Analysis Error: " + (err.detail || "Failed to run analysis"));
            btn.disabled = false;
            btn.innerHTML = `<i data-lucide="play" class="w-4 h-4 fill-white"></i><span>Run Verification & AI Analysis</span>`;
            if (window.lucide) lucide.createIcons();
            return;
        }
        window.location.reload();
    } catch (err) {
        alert("Request failed: " + err.message);
        btn.disabled = false;
    }
}

async function submitUploadFile(input) {
    if (!input.files || !input.files[0]) return;
    const file = input.files[0];
    const container = document.getElementById('case-container');
    if (!container) return;
    const caseId = container.dataset.caseId;

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch(`/api/v1/cases/${caseId}/evidence`, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            alert("Upload Failed: " + (err.detail || "Unknown error"));
            return;
        }
        window.location.reload();
    } catch (err) {
        alert("Upload error: " + err.message);
    }
}

async function handleRecordCallback(e) {
    e.preventDefault();
    const container = document.getElementById('case-container');
    if (!container) return;
    const caseId = container.dataset.caseId;

    const phone = document.getElementById('cb-phone').value.trim();
    const contact = document.getElementById('cb-contact').value.trim();
    const notes = document.getElementById('cb-notes').value.trim();

    try {
        const res = await fetch(`/api/v1/cases/${caseId}/record-verification`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                callback_phone_used: phone,
                vendor_contact_spoken: contact,
                confirmation_method: "Voice Phone Callback",
                is_confirmed: true,
                notes: notes
            })
        });

        if (!res.ok) {
            const err = await res.json();
            alert("Cedar Permission Denied: " + (err.detail || "Unable to record callback"));
            return;
        }
        alert("Out-of-band verification callback recorded! Re-running analysis...");
        await fetch(`/api/v1/cases/${caseId}/analyze`, { method: 'POST' });
        window.location.reload();
    } catch (err) {
        alert("Error: " + err.message);
    }
}

async function handleOverrideHold(e) {
    e.preventDefault();
    const container = document.getElementById('case-container');
    if (!container) return;
    const caseId = container.dataset.caseId;

    const reason = document.getElementById('override-reason').value.trim();
    if (!reason) {
        alert("Documented override justification is mandatory under Cedar policy.");
        return;
    }

    try {
        const res = await fetch(`/api/v1/cases/${caseId}/override`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ override_reason: reason })
        });

        if (!res.ok) {
            const err = await res.json();
            alert("Cedar Authorization Failed: " + (err.detail || "Only Approvers can override holds"));
            return;
        }
        alert("Payment hold overridden under Approver authority.");
        window.location.reload();
    } catch (err) {
        alert("Error: " + err.message);
    }
}

async function handleApproveDisposition() {
    const container = document.getElementById('case-container');
    if (!container) return;
    const caseId = container.dataset.caseId;

    if (!confirm("Confirm approval to release payment disbursement through accounts payable?")) {
        return;
    }

    try {
        const res = await fetch(`/api/v1/cases/${caseId}/disposition`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes: "Approved for disbursement release" })
        });

        if (!res.ok) {
            const err = await res.json();
            alert("Approval Failed: " + (err.detail || "Unauthorized or invalid state"));
            return;
        }
        alert("Payment disbursement approved and closed.");
        window.location.reload();
    } catch (err) {
        alert("Error: " + err.message);
    }
}
