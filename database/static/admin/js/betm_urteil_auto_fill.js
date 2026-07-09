/**
 * Auto-Fill Funktionalität für BetmUrteil Admin Form
 * Nutzt die Gemini API um Betäubungsmittel-Urteilsfelder automatisch auszufüllen
 */

(function() {
    'use strict';

    // Warten bis DOM geladen ist
    document.addEventListener('DOMContentLoaded', function() {
        console.log('BetmUrteil Auto-Fill JavaScript geladen');

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

                // API Call für betmurteil auto-fill
                const response = await fetch('/admin/database/betmurteil/auto-fill/', {
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
            setFieldValue('id_deliktsertrag', data.deliktsertrag);
            setFieldValue('id_deliktsdauer_in_monaten', data.deliktsdauer_in_monaten);

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
            setSelectValue('id_rolle', data.rolle);

            // Nummer Felder
            setFieldValue('id_nebenverurteilungsscore', data.nebenverurteilungsscore);
            setFieldValue('id_freiheitsstrafe_in_monaten', data.freiheitsstrafe_in_monaten);
            setFieldValue('id_anzahl_tagessaetze', data.anzahl_tagessaetze);

            // Boolean Felder (Checkboxen)
            setCheckboxValue('id_mengenmaessig', data.mengenmaessig);
            setCheckboxValue('id_bandenmaessig', data.bandenmaessig);
            setCheckboxValue('id_gewerbsmaessig', data.gewerbsmaessig);
            setCheckboxValue('id_anstaltentreffen', data.anstaltentreffen);
            setCheckboxValue('id_mehrfach', data.mehrfach);
            setCheckboxValue('id_beschaffungskriminalitaet', data.beschaffungskriminalitaet);
            setCheckboxValue('id_vorbestraft', data.vorbestraft);
            setCheckboxValue('id_vorbestraft_einschlaegig', data.vorbestraft_einschlaegig);
            setCheckboxValue('id_in_ki_modell', data.in_ki_modell);

            // Spezialbehandlung Many-to-Many Feld betm
            if (data.betm) {
                showMessage('ℹ️ Extrahiertes Betäubungsmittel: <strong>' + data.betm + '</strong>. Bitte wählen Sie dieses (oder legen Sie es neu an) im Feld "Betm" aus.', 'warning');
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
         * Setzt den Wert eines Select-Feldes
         */
        function setSelectValue(fieldId, value) {
            const field = document.getElementById(fieldId);
            if (field && value) {
                // Exakte Übereinstimmung suchen
                for (let i = 0; i < field.options.length; i++) {
                    if (field.options[i].value === value || field.options[i].text === value) {
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
