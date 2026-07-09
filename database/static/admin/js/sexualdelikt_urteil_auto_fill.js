/**
 * Auto-Fill Funktionalität für SexualdeliktUrteil Admin Form
 * Nutzt die Gemini API um Sexualdelikt-Urteilsfelder automatisch auszufüllen
 */

(function() {
    'use strict';

    // Warten bis DOM geladen ist
    document.addEventListener('DOMContentLoaded', function() {
        console.log('SexualdeliktUrteil Auto-Fill JavaScript geladen');

        // Volltext und PDF-Link Input Felder finden
        const volltextField = document.getElementById('id_volltext_input');
        const pdfUrlField = document.getElementById('id_pdf_url_input');

        if (!volltextField) {
            console.warn('Volltext Input Feld nicht gefunden');
            return;
        }

        // Button für Auto-Fill erstellen
        const autoFillButton = document.createElement('button');
        autoFillButton.type = 'button';
        autoFillButton.className = 'button default';
        autoFillButton.style.marginTop = '10px';
        autoFillButton.style.marginBottom = '10px';
        autoFillButton.innerHTML = '🤖 Formular automatisch ausfüllen';
        autoFillButton.id = 'auto-fill-button';

        // Button nach dem entsprechenden Feld einfügen (bevorzugt nach dem PDF-Link Feld)
        const insertAfterField = pdfUrlField || volltextField;
        insertAfterField.parentNode.insertBefore(autoFillButton, insertAfterField.nextSibling);

        // Loading Spinner erstellen
        const loadingSpinner = document.createElement('div');
        loadingSpinner.id = 'auto-fill-loading';
        loadingSpinner.style.display = 'none';
        loadingSpinner.style.marginTop = '10px';
        loadingSpinner.innerHTML = '<span style="color: #417690;">⏳ Analysiere Urteil mit KI... Bitte warten...</span>';
        autoFillButton.parentNode.insertBefore(loadingSpinner, autoFillButton.nextSibling);

        // Message Container erstellen
        const messageContainer = document.createElement('div');
        messageContainer.id = 'auto-fill-messages';
        messageContainer.style.marginTop = '10px';
        loadingSpinner.parentNode.insertBefore(messageContainer, loadingSpinner.nextSibling);

        // Click Handler für Auto-Fill Button
        autoFillButton.addEventListener('click', async function() {
            const volltext = volltextField.value.trim();
            const pdfUrl = pdfUrlField ? pdfUrlField.value.trim() : '';

            // Validation
            if (!volltext && !pdfUrl) {
                showMessage('Bitte fügen Sie den Volltext ein ODER geben Sie einen PDF-Link an.', 'error');
                return;
            }

            if (volltext && volltext.length < 100) {
                showMessage('Der Text ist zu kurz. Bitte fügen Sie den kompletten Urteilstext ein.', 'error');
                return;
            }

            // UI State
            autoFillButton.disabled = true;
            loadingSpinner.style.display = 'block';
            if (pdfUrl && !volltext) {
                loadingSpinner.querySelector('span').innerHTML = '⏳ Lade PDF herunter und analysiere mit KI... Bitte warten...';
            } else {
                loadingSpinner.querySelector('span').innerHTML = '⏳ Analysiere Urteil mit KI... Bitte warten...';
            }
            messageContainer.innerHTML = '';

            try {
                // CSRF Token holen
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

                // Payload erstellen
                const payload = {};
                if (volltext) payload.volltext = volltext;
                if (pdfUrl) payload.pdf_url = pdfUrl;

                // API Call für sexualdelikturteil auto-fill
                const response = await fetch('/admin/database/sexualdelikturteil/auto-fill/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(payload)
                });

                const result = await response.json();

                if (result.success) {
                    // Formular ausfüllen
                    fillFormFields(result.data);

                    // Success Message
                    let message = result.message || 'Formular erfolgreich ausgefüllt!';
                    showMessage(message, 'success');

                    // Warnungen anzeigen, falls vorhanden
                    if (result.warnings && result.warnings.length > 0) {
                        showMessage('Validierungswarnungen:', 'warning');
                        result.warnings.forEach(warning => {
                            showMessage('⚠️ ' + warning, 'warning');
                        });
                    }

                    // Scroll zum ersten Feld
                    document.getElementById('id_fall_nr').scrollIntoView({ behavior: 'smooth', block: 'center' });

                } else {
                    showMessage('Fehler: ' + (result.error || 'Unbekannter Fehler'), 'error');
                }

            } catch (error) {
                console.error('Auto-Fill Error:', error);
                showMessage('Fehler bei der Verarbeitung: ' + error.message, 'error');
            } finally {
                autoFillButton.disabled = false;
                loadingSpinner.style.display = 'none';
            }
        });

        /**
         * Füllt die Formularfelder mit den extrahierten Daten
         */
        function fillFormFields(data) {
            console.log('Fülle Formularfelder aus:', data);

            // Text Felder
            setFieldValue('id_fall_nr', data.fall_nr);
            setFieldValue('id_gericht', data.gericht);
            setFieldValue('id_url_link', data.url_link);
            setFieldValue('id_zusammenfassung', data.zusammenfassung);
            setFieldValue('id_hautpdelikt_deliktsdauer_einfachbegehung', data.hautpdelikt_deliktsdauer_einfachbegehung);
            setFieldValue('id_hauptdelikt_mehrfachbegehung_deliktsperiode', data.hauptdelikt_mehrfachbegehung_deliktsperiode);

            // Datum
            if (data.urteilsdatum) {
                setFieldValue('id_urteilsdatum', data.urteilsdatum);
            }

            // Select/Dropdown Felder
            setSelectValue('id_geschlecht', data.geschlecht);
            setSelectValue('id_nationalitaet', data.nationalitaet);
            setSelectValue('id_hauptsanktion', data.hauptsanktion);
            setSelectValue('id_vollzug', data.vollzug);
            setSelectValue('id_verfahrensart', data.verfahrensart);
            setSelectValue('id_kanton', data.kanton);
            setSelectValue('id_hauptdelikt', data.hauptdelikt);
            setSelectValue('id_hauptdelikt_tatmittel', data.hauptdelikt_tatmittel);
            setSelectValue('id_hauptdelikt_taeter_opfer_beziehung', data.hauptdelikt_taeter_opfer_beziehung);
            setSelectValue('id_hauptdelikt_opferalter', data.hauptdelikt_opferalter);
            setSelectValue('id_hauptdelikt_opfer_vorerfahrung', data.hauptdelikt_opfer_vorerfahrung);

            // Boolean Select Felder (Ja/Nein Choice fields)
            setSelectValue('id_hauptdelikt_mehrfachbegehung', data.hauptdelikt_mehrfachbegehung);
            setSelectValue('id_hauptdelikt_deliktsdauer_bekannt', data.hauptdelikt_deliktsdauer_bekannt);
            setSelectValue('id_vorbestraft', data.vorbestraft);
            setSelectValue('id_vorbestraft_einschlaegig', data.vorbestraft_einschlaegig);

            // Nummer Felder
            setFieldValue('id_deliktssscore_uebrige_delikte', data.deliktsscore_uebrige_delikte);
            setFieldValue('id_hauptdelikt_mehrfachbegehung_anzahl', data.hauptdelikt_mehrfachbegehung_anzahl);
            setFieldValue('id_freiheitsstrafe_in_monaten', data.freiheitsstrafe_in_monaten);
            setFieldValue('id_anzahl_tagessaetze', data.anzahl_tagessaetze);

            // Checkbox Felder (falls vorhanden)
            setCheckboxValue('id_in_ki_modell', data.in_ki_modell);

            // Spezialbehandlung Many-to-Many / Text fields
            if (data.weitere_sexualdelikte) {
                showMessage('ℹ️ Weitere Sexualdelikte: <strong>' + data.weitere_sexualdelikte + '</strong>. Bitte wählen Sie diese im Feld "Weitere Sexualdelikte" aus.', 'warning');
            }
            if (data.besonderheiten) {
                showMessage('ℹ️ Besonderheiten: <strong>' + data.besonderheiten + '</strong>. Bitte wählen Sie diese im Feld "Besonderheiten" aus.', 'warning');
            }

            // Highlight gefüllte Felder kurz
            highlightFilledFields();
        }

        /**
         * Setzt den Wert eines Input-Feldes
         */
        function setFieldValue(fieldId, value) {
            const field = document.getElementById(fieldId);
            if (field && value !== undefined && value !== null) {
                field.value = value;
                field.classList.add('auto-filled');
            }
        }

        /**
         * Setzt den Wert eines Select-Feldes (robust für strings, ids, und booleans)
         */
        function setSelectValue(fieldId, value) {
            const field = document.getElementById(fieldId);
            if (field && value !== undefined && value !== null) {
                let stringValue = String(value).toLowerCase();
                if (value === true) stringValue = 'true';
                if (value === false) stringValue = 'false';

                for (let i = 0; i < field.options.length; i++) {
                    const optVal = field.options[i].value.toLowerCase();
                    const optText = field.options[i].text.toLowerCase();
                    
                    if (optVal === stringValue || optText === stringValue ||
                        (stringValue === 'true' && optText === 'ja') ||
                        (stringValue === 'false' && optText === 'nein')) {
                        field.selectedIndex = i;
                        field.classList.add('auto-filled');
                        return;
                    }
                }
                console.warn(`Wert "${value}" nicht gefunden für Select-Feld ${fieldId}`);
            }
        }

        /**
         * Setzt den Wert einer Checkbox
         */
        function setCheckboxValue(fieldId, value) {
            const field = document.getElementById(fieldId);
            if (field) {
                field.checked = Boolean(value);
                if (value) {
                    field.classList.add('auto-filled');
                }
            }
        }

        /**
         * Highlightet gefüllte Felder kurz
         */
        function highlightFilledFields() {
            const filledFields = document.querySelectorAll('.auto-filled');
            filledFields.forEach(field => {
                field.style.transition = 'background-color 0.5s';
                field.style.backgroundColor = '#c7f5c7';

                setTimeout(() => {
                    field.style.backgroundColor = '';
                    setTimeout(() => {
                        field.classList.remove('auto-filled');
                    }, 500);
                }, 2000);
            });
        }

        /**
         * Zeigt eine Nachricht an
         */
        function showMessage(text, type) {
            const messageDiv = document.createElement('div');
            messageDiv.style.padding = '10px';
            messageDiv.style.marginTop = '5px';
            messageDiv.style.borderRadius = '4px';

            switch(type) {
                case 'success':
                    messageDiv.style.backgroundColor = '#d4edda';
                    messageDiv.style.color = '#155724';
                    messageDiv.style.border = '1px solid #c3e6cb';
                    messageDiv.innerHTML = '✅ ' + text;
                    break;
                case 'error':
                    messageDiv.style.backgroundColor = '#f8d7da';
                    messageDiv.style.color = '#721c24';
                    messageDiv.style.border = '1px solid #f5c6cb';
                    messageDiv.innerHTML = '❌ ' + text;
                    break;
                case 'warning':
                    messageDiv.style.backgroundColor = '#fff3cd';
                    messageDiv.style.color = '#856404';
                    messageDiv.style.border = '1px solid #ffeaa7';
                    messageDiv.innerHTML = text;
                    break;
            }

            messageContainer.appendChild(messageDiv);

            // Auto-remove nach 10 Sekunden (außer bei Warnungen)
            if (type !== 'warning') {
                setTimeout(() => {
                    messageDiv.style.transition = 'opacity 0.5s';
                    messageDiv.style.opacity = '0';
                    setTimeout(() => messageDiv.remove(), 500);
                }, 10000);
            }
        }
    });
})();
