document.addEventListener('DOMContentLoaded', function () {
    const button = document.getElementById('insert-link');
    const textarea = document.querySelector('.editor-textarea');

    if (!button || !textarea) {
        return;
    }

    button.addEventListener('click', function () {
        const url = prompt('Enter the URL to link to:');
        if (!url) {
            return;
        }
        const selectedText = textarea.value.substring(textarea.selectionStart, textarea.selectionEnd) || 'link text';
        const linkSyntax = `<a href="${url}" target="_blank">${selectedText}</a>`;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        textarea.value = textarea.value.substring(0, start) + linkSyntax + textarea.value.substring(end);
    });
});
