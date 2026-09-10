/**
 * Chat-Komponente für die Präjudizensuche (Alpine.js).
 * apiHistory: rohe Anthropic-messages, unverändert vom Server übernommen und beim nächsten
 *   POST mitgeschickt - der Server hält keinen Konversations-State.
 * visibleMessages: fürs UI aufbereitete {id, role, text}.
 */
function praejudizenChat() {
    return {
        input: '',
        loading: false,
        errorMsg: '',
        apiHistory: [],
        conversationId: null,
        visibleMessages: [],

        init() {
            this.conversationId = crypto.randomUUID();
        },

        async send() {
            const text = this.input.trim();
            if (!text || this.loading) {
                return;
            }
            this.errorMsg = '';
            this.visibleMessages.push({id: crypto.randomUUID(), role: 'user', text: text});
            this.input = '';
            this.loading = true;
            this.$nextTick(() => this.scrollDown());

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            try {
                const response = await fetch('/praejudizensuche/nachricht', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify({
                        history: this.apiHistory,
                        message: text,
                        conversation_id: this.conversationId,
                    }),
                });
                const result = await response.json();
                if (!response.ok || !result.success) {
                    this.errorMsg = result.error || 'Unbekannter Fehler.';
                } else {
                    this.apiHistory = result.history;
                    this.conversationId = result.conversation_id;
                    this.visibleMessages.push({id: crypto.randomUUID(), role: 'assistant', text: result.reply});
                }
            } catch (e) {
                this.errorMsg = 'Verbindungsfehler. Bitte erneut versuchen.';
            } finally {
                this.loading = false;
                this.$nextTick(() => this.scrollDown());
            }
        },

        scrollDown() {
            const el = this.$refs.messagesEl;
            if (el) {
                el.scrollTop = el.scrollHeight;
            }
        },
    };
}
