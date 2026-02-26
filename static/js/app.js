/**
 * QR Forge — Frontend Logic
 */
(function () {
    "use strict";

    // ---- DOM Elements ----
    const typeTabs = document.querySelectorAll(".type-tab");
    const dataFields = document.getElementById("dataFields");
    const moduleStyle = document.getElementById("moduleStyle");
    const colorStyle = document.getElementById("colorStyle");
    const fgColor = document.getElementById("fgColor");
    const bgColor = document.getElementById("bgColor");
    const gradientEnd = document.getElementById("gradientEnd");
    const gradientGroup = document.getElementById("gradientGroup");
    const fgHex = document.getElementById("fgHex");
    const bgHex = document.getElementById("bgHex");
    const gradHex = document.getElementById("gradHex");
    const errorCorrection = document.getElementById("errorCorrection");
    const outputFormat = document.getElementById("outputFormat");
    const logoInput = document.getElementById("logoInput");
    const logoUploadArea = document.getElementById("logoUploadArea");
    const logoPlaceholder = document.getElementById("logoPlaceholder");
    const logoPreviewWrap = document.getElementById("logoPreviewWrap");
    const logoPreview = document.getElementById("logoPreview");
    const removeLogo = document.getElementById("removeLogo");
    const generateBtn = document.getElementById("generateBtn");
    const previewEmpty = document.getElementById("previewEmpty");
    const previewLoading = document.getElementById("previewLoading");
    const previewResult = document.getElementById("previewResult");
    const previewImg = document.getElementById("previewImg");
    const downloadActions = document.getElementById("downloadActions");
    const downloadBtn = document.getElementById("downloadBtn");
    const downloadPng = document.getElementById("downloadPng");
    const downloadSvg = document.getElementById("downloadSvg");
    const downloadPdf = document.getElementById("downloadPdf");
    const toast = document.getElementById("toast");
    const toastMsg = document.getElementById("toastMsg");

    let activeType = "url";
    let uploadedLogoFilename = null;
    let lastGeneratedFilename = null;

    // ---- Field Definitions per QR Type ----
    const FIELD_DEFS = {
        url: [
            { key: "url", label: "URL", type: "url", placeholder: "https://example.com", required: true },
        ],
        text: [
            { key: "text", label: "Text Content", type: "textarea", placeholder: "Enter any text...", required: true },
            { key: "_iosCompat", label: "", type: "checkbox", checkboxLabel: "Make iPhone compatible (wraps text as URL)" },
            { key: "_iosNote", type: "note", message: "⚠️ iPhone Camera & Code Scanner cannot read plain text QR codes. Enable the option above to wrap your text as a URL that works everywhere." },
        ],
        wifi: [
            { key: "ssid", label: "Network Name (SSID)", type: "text", placeholder: "MyWiFi", required: true },
            { key: "password", label: "Password", type: "text", placeholder: "••••••••" },
            {
                key: "encryption", label: "Encryption", type: "select", options: [
                    { value: "WPA", label: "WPA/WPA2" },
                    { value: "WEP", label: "WEP" },
                    { value: "nopass", label: "None" },
                ]
            },
            { key: "hidden", label: "", type: "checkbox", checkboxLabel: "Hidden Network" },
        ],
        vcard: [
            { key: "fullName", label: "Full Name", type: "text", placeholder: "John Doe", required: true },
            { key: "org", label: "Organization", type: "text", placeholder: "Acme Inc." },
            { key: "title", label: "Job Title", type: "text", placeholder: "Software Engineer" },
            { key: "phone", label: "Phone", type: "tel", placeholder: "+1 555-0123" },
            { key: "email", label: "Email", type: "email", placeholder: "john@example.com" },
            { key: "website", label: "Website", type: "url", placeholder: "https://johndoe.com" },
            { key: "address", label: "Address", type: "text", placeholder: "123 Main St, City" },
        ],
        email: [
            { key: "to", label: "Email Address", type: "email", placeholder: "hello@example.com", required: true },
            { key: "subject", label: "Subject", type: "text", placeholder: "Meeting Follow-up" },
            { key: "body", label: "Body", type: "textarea", placeholder: "Hi, ..." },
        ],
        sms: [
            { key: "phone", label: "Phone Number", type: "tel", placeholder: "+1 555-0123", required: true },
            { key: "message", label: "Message", type: "textarea", placeholder: "Hey! Check this out..." },
        ],
        phone: [
            { key: "phone", label: "Phone Number", type: "tel", placeholder: "+1 555-0123", required: true },
        ],
        event: [
            { key: "title", label: "Event Title", type: "text", placeholder: "Team Meeting", required: true },
            { key: "location", label: "Location", type: "text", placeholder: "Conference Room A" },
            { key: "startDate", label: "Start", type: "datetime-local", required: true },
            { key: "endDate", label: "End", type: "datetime-local" },
            { key: "description", label: "Description", type: "textarea", placeholder: "Agenda notes..." },
        ],
    };

    // ---- Render Data Fields ----
    function renderFields(type) {
        const fields = FIELD_DEFS[type] || [];
        dataFields.innerHTML = "";
        fields.forEach((f) => {
            const group = document.createElement("div");
            group.className = "form-group";

            if (f.type === "note") {
                group.innerHTML = `
                    <div style="padding:10px 14px;background:rgba(234,179,8,0.08);border:1px solid rgba(234,179,8,0.2);border-radius:6px;font-size:0.78rem;color:#eab308;line-height:1.5;">
                        ${f.message}
                    </div>
                `;
            } else if (f.type === "checkbox") {
                group.innerHTML = `
                    <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
                        <input type="checkbox" id="field_${f.key}" data-key="${f.key}" style="accent-color:var(--accent);width:16px;height:16px;" ${f.key === '_iosCompat' ? 'checked' : ''}>
                        <span style="font-size:0.85rem;color:var(--text-secondary);">${f.checkboxLabel}</span>
                    </label>
                `;
            } else if (f.type === "select") {
                const optionsHTML = f.options
                    .map((o) => `<option value="${o.value}">${o.label}</option>`)
                    .join("");
                group.innerHTML = `
                    <label>${f.label}</label>
                    <select id="field_${f.key}" data-key="${f.key}">${optionsHTML}</select>
                `;
            } else if (f.type === "textarea") {
                group.innerHTML = `
                    <label>${f.label}${f.required ? ' <span style="color:var(--error)">*</span>' : ""}</label>
                    <textarea id="field_${f.key}" data-key="${f.key}" placeholder="${f.placeholder || ""}" ${f.required ? "required" : ""}></textarea>
                `;
            } else {
                group.innerHTML = `
                    <label>${f.label}${f.required ? ' <span style="color:var(--error)">*</span>' : ""}</label>
                    <input type="${f.type}" id="field_${f.key}" data-key="${f.key}" placeholder="${f.placeholder || ""}" ${f.required ? "required" : ""}>
                `;
            }

            dataFields.appendChild(group);
        });
    }

    // ---- Collect Data Fields ----
    function collectData() {
        const data = {};
        const inputs = dataFields.querySelectorAll("[data-key]");
        inputs.forEach((el) => {
            if (el.type === "checkbox") {
                data[el.dataset.key] = el.checked;
            } else {
                data[el.dataset.key] = el.value;
            }
        });
        return data;
    }

    // ---- Validate Required ----
    function validate() {
        const fields = FIELD_DEFS[activeType] || [];
        for (const f of fields) {
            if (f.required) {
                const el = document.getElementById(`field_${f.key}`);
                if (!el || !el.value.trim()) {
                    showToast(`Please fill in: ${f.label}`, "error");
                    el && el.focus();
                    return false;
                }
            }
        }
        return true;
    }

    // ---- Toast ----
    function showToast(msg, type = "error") {
        toastMsg.textContent = msg;
        toast.className = "toast show" + (type === "success" ? " success" : "");
        clearTimeout(toast._timer);
        toast._timer = setTimeout(() => { toast.className = "toast"; }, 3500);
    }

    // ---- Tab Switching ----
    typeTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            typeTabs.forEach((t) => t.classList.remove("active"));
            tab.classList.add("active");
            activeType = tab.dataset.type;
            renderFields(activeType);
        });
    });

    // ---- Color Style Toggle ----
    colorStyle.addEventListener("change", () => {
        gradientGroup.style.display = colorStyle.value === "solid" ? "none" : "flex";
    });

    // ---- Color Hex Display ----
    fgColor.addEventListener("input", () => { fgHex.textContent = fgColor.value.toUpperCase(); });
    bgColor.addEventListener("input", () => { bgHex.textContent = bgColor.value.toUpperCase(); });
    gradientEnd.addEventListener("input", () => { gradHex.textContent = gradientEnd.value.toUpperCase(); });

    // ---- Logo Upload ----
    logoUploadArea.addEventListener("click", () => logoInput.click());
    logoUploadArea.addEventListener("dragover", (e) => { e.preventDefault(); logoUploadArea.style.borderColor = "var(--accent)"; });
    logoUploadArea.addEventListener("dragleave", () => { logoUploadArea.style.borderColor = ""; });
    logoUploadArea.addEventListener("drop", (e) => {
        e.preventDefault();
        logoUploadArea.style.borderColor = "";
        if (e.dataTransfer.files.length > 0) {
            handleLogoFile(e.dataTransfer.files[0]);
        }
    });
    logoInput.addEventListener("change", () => {
        if (logoInput.files.length > 0) handleLogoFile(logoInput.files[0]);
    });

    async function handleLogoFile(file) {
        if (!file.type.startsWith("image/")) {
            showToast("Please upload an image file");
            return;
        }

        // Show local preview
        const reader = new FileReader();
        reader.onload = (e) => {
            logoPreview.src = e.target.result;
            logoPlaceholder.style.display = "none";
            logoPreviewWrap.style.display = "flex";
        };
        reader.readAsDataURL(file);

        // Upload to server
        const formData = new FormData();
        formData.append("logo", file);
        try {
            const res = await fetch("/upload-logo", { method: "POST", body: formData });
            const json = await res.json();
            if (json.success) {
                uploadedLogoFilename = json.filename;
                showToast("Logo uploaded!", "success");
                // Auto-set error correction to High
                errorCorrection.value = "H";
            } else {
                showToast(json.error || "Upload failed");
            }
        } catch (err) {
            showToast("Upload failed: " + err.message);
        }
    }

    removeLogo.addEventListener("click", (e) => {
        e.stopPropagation();
        uploadedLogoFilename = null;
        logoInput.value = "";
        logoPlaceholder.style.display = "flex";
        logoPreviewWrap.style.display = "none";
    });

    // ---- Generate QR ----
    generateBtn.addEventListener("click", () => generateQR(outputFormat.value));

    async function generateQR(format) {
        if (!validate()) return;

        generateBtn.disabled = true;
        previewEmpty.style.display = "none";
        previewResult.style.display = "none";
        previewLoading.style.display = "flex";
        downloadActions.style.display = "none";

        const payload = {
            qr_type: activeType,
            data: collectData(),
            fg_color: fgColor.value,
            bg_color: bgColor.value,
            gradient_end: colorStyle.value !== "solid" ? gradientEnd.value : null,
            color_style: colorStyle.value,
            module_style: moduleStyle.value,
            error_correction: errorCorrection.value,
            logo_filename: uploadedLogoFilename,
            output_format: format || "png",
            size: 20,
            border: 4,
        };

        try {
            const res = await fetch("/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const json = await res.json();

            if (json.success) {
                lastGeneratedFilename = json.filename;
                previewLoading.style.display = "none";

                if (format === "pdf") {
                    // For PDF, show a success message and trigger download
                    previewResult.innerHTML = `
                        <div style="text-align:center;padding:40px 20px;">
                            <svg viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2" style="width:56px;height:56px;margin-bottom:16px;">
                                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                                <polyline points="22 4 12 14.01 9 11.01"/>
                            </svg>
                            <p style="font-weight:600;font-size:1.1rem;margin-bottom:6px;">PDF Generated!</p>
                            <p style="color:var(--text-secondary);font-size:0.85rem;">Click download to save</p>
                        </div>
                    `;
                    previewResult.style.display = "block";
                } else if (format === "svg") {
                    // For SVG, display it in an img tag
                    previewImg.src = json.file_url + "?t=" + Date.now();
                    previewResult.innerHTML = '';
                    previewResult.appendChild(previewImg);
                    previewResult.style.display = "block";
                } else {
                    previewImg.src = json.file_url + "?t=" + Date.now();
                    previewResult.innerHTML = '';
                    previewResult.appendChild(previewImg);
                    previewResult.style.display = "block";
                }

                downloadBtn.href = json.download_url;
                // Add view link for easy scanning
                const viewUrl = `/view/${json.filename}`;
                let viewLink = document.getElementById('viewLink');
                if (!viewLink) {
                    viewLink = document.createElement('a');
                    viewLink.id = 'viewLink';
                    viewLink.className = 'download-btn secondary';
                    viewLink.target = '_blank';
                    viewLink.textContent = '⛶ Scan';
                    viewLink.title = 'Open full-screen for easy scanning';
                    downloadActions.appendChild(viewLink);
                }
                viewLink.href = viewUrl;
                downloadActions.style.display = "flex";
                showToast("QR code generated successfully!", "success");
            } else {
                throw new Error(json.error || "Generation failed");
            }
        } catch (err) {
            previewLoading.style.display = "none";
            previewEmpty.style.display = "flex";
            showToast("Error: " + err.message);
        } finally {
            generateBtn.disabled = false;
        }
    }

    // ---- Quick Format Downloads ----
    async function quickDownload(format) {
        if (!validate()) return;
        await generateQR(format);
    }

    downloadPng.addEventListener("click", () => quickDownload("png"));
    downloadSvg.addEventListener("click", () => quickDownload("svg"));
    downloadPdf.addEventListener("click", () => quickDownload("pdf"));

    // ---- Initialize ----
    renderFields(activeType);

})();
