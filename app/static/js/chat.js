const urlConversationId = window.location.pathname.split('/').pop();
let username = '';

let currentConversationId = '';
let currentContextMenuId = null;

let animationTimeouts = [];
let isResponding = false;

function logout() {
    if (confirm("Are you sure you want to log out?")) {
        fetch('/auth/logout', {
            method: 'POST'
        }).then(response => {
            if (response.ok) {
                window.location.href = '/auth/login';
            }
        });
    }
}

function toggleUserMenu() {
    const menu = document.getElementById('user-menu');
    const button = document.querySelector('.user-profile-button');

    menu.classList.toggle('hidden');

    if (!menu.classList.contains('hidden')) {
        const buttonRect = button.getBoundingClientRect();
        const sidebarRect = document.querySelector('.sidebar').getBoundingClientRect();
        
        menu.style.left = `${buttonRect.left}px`;
        menu.style.bottom = `${window.innerHeight - buttonRect.top}px`;
        menu.style.width = `${buttonRect.width}px`;

        const menuItems = menu.querySelectorAll('.user-menu-item');

        menuItems.forEach(item => {
            item.style.width = `${buttonRect.width}px`;
        });
    }
}

function toggleModelDropdown() {
    const dropdown = document.getElementById('model-dropdown');
    dropdown.classList.toggle('hidden');

    if (!dropdown.classList.contains('hidden')) {
        document.addEventListener('click', function closeDropdown(e) {
            if (!e.target.closest('.dropdown')) {
                dropdown.classList.add('hidden');
                document.removeEventListener('click', closeDropdown);
            }
        });
    }
}

function toggleSearchBar() {
    document.getElementById('conversation-search').classList.toggle('hidden');
}

function selectModel(model) {
    document.getElementById('current-model').innerText = model;
    var links = document.querySelectorAll('.dropdown-content a');

    links.forEach(link => {
        if (link.innerText === model)
            link.classList.add('selected');
        else
            link.classList.remove('selected');
    });

    document.getElementById('send-button').disabled = false;

    document.getElementById('model-dropdown').classList.add('hidden');
}

function createConversation() {
    fetch('/create_conversation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })

    .then(response => response.json())
    .then(data => {
        loadConversationList()

        .then(() => {
            selectConversation(data.conversation_id);
        });
    });
}

function selectConversation(conversationId) {
    if (currentConversationId === conversationId)
        return;

    currentConversationId = conversationId;
    var buttons = document.querySelectorAll('.conversation-button');

    buttons.forEach(btn => {
        if (btn.getAttribute('data-conversation-id') === conversationId)
            btn.classList.add('selected');
        else
            btn.classList.remove('selected');
    });

    const chatContent = document.getElementById('chat-content');
    chatContent.innerHTML = '';

    loadConversation(conversationId);
    window.history.pushState({}, '', `/chat/${conversationId}`);
}

function toggleSendButton() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');

    if (messageInput.value.trim() !== '')
        sendButton.classList.add('active');
    else
        sendButton.classList.remove('active');
}

function createUserMessage(message, username, modelName, files = []) {
    const messageContainer = document.createElement('div');
    messageContainer.className = 'message-container user-message';

    const userIcon = document.createElement('div');

    userIcon.className = 'user-icon';
    userIcon.innerText = getUserInitials(username);
    userIcon.style.backgroundColor = getComputedStyle(document.documentElement)
        .getPropertyValue('--user-color').trim();

    const userInfo = document.createElement('div');

    userInfo.className = 'user-info';
    userInfo.innerText = username;

    const textContent = document.createElement('div');
    textContent.className = 'message-content';
    
    if (message.indexOf('<tag>') !== -1)
        textContent.innerHTML = renderTags(message);
    else
        textContent.innerText = message;

    const messageHeader = document.createElement('div');

    messageHeader.className = 'message-header';
    messageHeader.appendChild(userIcon);
    messageHeader.appendChild(userInfo);

    messageContainer.appendChild(messageHeader);
    
    if (files.length > 0) {
        const attachments = document.createElement('div');
        attachments.className = 'message-attachments';
        
        files.forEach(file => {
            const attachment = document.createElement('div');
            attachment.className = 'message-attachment';
            
            const icon = document.createElement('div');

            icon.className = 'file-icon';
            icon.innerText = file.extension;
            icon.style.backgroundColor = file.color;
            
            const fileName = document.createElement('div');

            fileName.className = 'file-name';
            fileName.innerText = file.name;
            
            attachment.appendChild(icon);
            attachment.appendChild(fileName);
            attachments.appendChild(attachment);
        });
        
        messageContainer.appendChild(textContent);
        messageContainer.appendChild(attachments);
    } else
        messageContainer.appendChild(textContent);
    
    return messageContainer;
}

function createAIMessage(message, modelName, animate = false) {
    const messageContainer = document.createElement('div');
    messageContainer.className = 'message-container ai-message';

    const aiIcon = document.createElement('div');

    aiIcon.className = 'ai-icon';
    aiIcon.innerHTML = '<img src="/static/images/microsoft_azure.png" alt="AI">';

    const aiInfo = document.createElement('div');

    aiInfo.className = 'user-info';
    aiInfo.innerText = modelName;

    const textContent = document.createElement('div');
    textContent.className = 'message-content';
    
    if (message.indexOf('<tag>') !== -1)
        textContent.innerHTML = renderTags(message);
    else
        textContent.innerText = message;

    const formattedMessage = message;
    textContent.setAttribute('data-full-text', formattedMessage);

    const messageHeader = document.createElement('div');

    messageHeader.className = 'message-header';
    messageHeader.appendChild(aiIcon);
    messageHeader.appendChild(aiInfo);

    messageContainer.appendChild(messageHeader);
    messageContainer.appendChild(textContent);

    if (animate) {
        document.getElementById('send-icon').classList.add('hidden');
        document.getElementById('cancel-icon').classList.remove('hidden');
        document.getElementById('send-button').classList.add('cancel-active');
        document.getElementById('send-button').classList.remove('active');
        document.getElementById('send-button').disabled = false;

        textContent.innerHTML = '';

        setTimeout(() => animateFormattedHTML(textContent, formattedMessage), 100);
    } else
        textContent.innerHTML = formattedMessage;

    return messageContainer;
}

function animateFormattedHTML(container, html, baseSpeed = 1) {
    isResponding = true;
    toggleSendButton();

    container.classList.add('animating');

    const docFrag = parseHTMLToFragment(html);
    container.innerHTML = '';

    animateNodes(container, docFrag.childNodes, baseSpeed);
}

function parseHTMLToFragment(html) {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;

    const frag = document.createDocumentFragment();

    while (tempDiv.firstChild)
        frag.appendChild(tempDiv.firstChild);

    return frag;
}

function animateNodes(container, nodes, baseSpeed) {
    if (!nodes || !nodes.length) {
        finalizeAnimation(container);
        return;
    }

    const node = nodes[0];
    nodes = Array.prototype.slice.call(nodes, 1);

    if (node.nodeType === Node.TEXT_NODE)
        animateTextNode(container, node.nodeValue, () => animateNodes(container, nodes, baseSpeed), baseSpeed);
    else {
        const clone = node.cloneNode(false);
        container.appendChild(clone);

        if (node.childNodes && node.childNodes.length > 0)
            animateNodes(clone, node.childNodes, baseSpeed);
        
        setTimeout(() => animateNodes(container, nodes, baseSpeed), 0);
    }
}

function animateTextNode(container, text, onComplete, baseSpeed) {
    let index = 0;

    function typeChar() {
        if (index < text.length) {
            container.appendChild(document.createTextNode(text[index]));

            let delay = baseSpeed;

            if ('.!?'.includes(text[index]))
                delay *= 4;
            
            else if (',;:'.includes(text[index]))
                delay *= 2.5;
            
            else if (' '.includes(text[index]))
                delay *= 1.5;

            index++;
            delay *= 0.5 + Math.random();

            const timeoutId = setTimeout(typeChar, delay);
            animationTimeouts.push(timeoutId);
        } else
            onComplete();
    }

    typeChar();
}

function finalizeAnimation(container) {
    container.classList.remove('animating');

    document.getElementById('send-icon').classList.remove('hidden');
    document.getElementById('cancel-icon').classList.add('hidden');
    document.getElementById('send-button').classList.remove('cancel-active');
    
    const messageInput = document.getElementById('message-input');

    if (messageInput.value.trim() !== '')
        document.getElementById('send-button').classList.add('active');
    
    isResponding = false;
    toggleSendButton();
}

function cancelAnimation() {
    animationTimeouts.forEach(timeoutId => clearTimeout(timeoutId));
    animationTimeouts = [];

    const animatingElements = document.querySelectorAll('.message-content.animating');
    
    animatingElements.forEach(element => {
        element.classList.remove('animating');
        element.innerHTML = element.getAttribute('data-full-text');
    });

    const sendIcon = document.getElementById('send-icon');
    const cancelIcon = document.getElementById('cancel-icon');
    const sendButton = document.getElementById('send-button');
    const messageInput = document.getElementById('message-input');

    sendIcon.classList.remove('hidden');
    cancelIcon.classList.add('hidden');
    sendButton.classList.remove('cancel-active');
    
    if (messageInput.value.trim() !== '')
        sendButton.classList.add('active');
    else
        sendButton.classList.remove('active');

    isResponding = false;
    toggleSendButton();

    sendButton.disabled = false;
}

function getUserInitials(username = '') {
    const names = username.split(' ');
    const firstInitial = names[0] ? names[0][0] : '';
    const lastInitial = names[1] ? names[1][0] : '';

    return (firstInitial + lastInitial).toUpperCase();
}

function processTags(message) {
    const whitelist = ['research', 'canvas', 'graph'];

    return message.replace(/@(\w+)/g, (match, word) => {
        if (whitelist.includes(word))
            return `<tag>${word}</tag>`;
        
        return match;
    });
}

function cleanTags(message) {
    return message.replace(/<\/?tag>/g, '');
}

const tagColorTable = {
    "research": 'rgba(153, 119, 252, 0.3)',  // purple
    "canvas": 'rgba(111, 119, 252, 0.3)',    // blue
    "graph": 'rgba(107, 246, 162, 0.3)'      // green
};

function renderTags(message) {
    return message.replace(/<tag>(.*?)<\/tag>/g, (match, word) => {
        const color = tagColorTable[word.toLowerCase()] || '#e0e0e0';
        return `<span class="tagged-text" style="background-color: ${color};">@${word}</span>`;
    });
}

function sendMessage() {
    const messageInput = document.getElementById('message-input');
    let message = messageInput.value.trim();
    
    message = processTags(message);
    
    const plainMessage = message;
    const selectedModel = document.getElementById('current-model').innerText;

    if (plainMessage === '' || !currentConversationId || isResponding)
        return;

    const fileDisplay = document.getElementById('file-display');
    const files = Array.from(fileDisplay.children).map(file => ({
        name: file.querySelector('.file-name').innerText,
        extension: file.querySelector('.file-icon').innerText,
        color: file.querySelector('.file-icon').style.backgroundColor
    }));
    
    const userMessageElement = createUserMessage(plainMessage, username, selectedModel, files);
    const chatContent = document.getElementById('chat-content');

    chatContent.appendChild(userMessageElement);
    chatContent.scrollTop = chatContent.scrollHeight;

    messageInput.value = '';

    toggleSendButton();

    fileDisplay.innerHTML = '';
    fileDisplay.classList.remove('has-files');

    document.getElementById('file-input').value = '';

    const sendButton = document.getElementById('send-button');

    sendButton.disabled = true;
    sendButton.classList.remove('active');

    isResponding = true;

    fetch('/send_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            message: plainMessage,
            conversation_id: currentConversationId, 
            model: selectedModel,
            files: files
        })
    })
    .then(response => response.json())
    .then(data => {
        const isError = data.response.status === 'error';
        const aiMessageElement = createAIMessage(data.response.response, selectedModel, !isError);

        chatContent.appendChild(aiMessageElement);
        chatContent.scrollTop = chatContent.scrollHeight;

        if (!isError) {
            isResponding = true;
            toggleSendButton();
        } else {
            isResponding = false;
            sendButton.disabled = false;
        }
    });
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !isResponding) {
        event.preventDefault();
        sendMessage();
    }
}

function getConversations() {
    return fetch('/get_conversations').then(response => response.json());
}

function loadConversation(conversationId) {
    getConversations()
    .then(data => {
        var chatContent = document.getElementById('chat-content');
        chatContent.innerHTML = '';

        var convoObject = data[conversationId] || {};
        var conversation = convoObject.conversation || [];

        conversation.forEach(message => {
            const messageElement = message.role === 'user' 
                ? createUserMessage(message.content[0].text, username, message.model, message.files || [])
                : createAIMessage(message.content[0].text, message.model, false);

            chatContent.appendChild(messageElement);
        });

        chatContent.scrollTop = chatContent.scrollHeight;
    });
}

function loadConversationList() {
    return getConversations()

    .then(data => {
        var conversationList = document.getElementById('conversation-list');
        conversationList.innerHTML = '';

        Object.keys(data).forEach(conversationId => {
            var conversationName = data[conversationId].name || "New Chat";
            var conversationItem = document.createElement('div');

            conversationItem.className = 'conversation-item';

            var button = document.createElement('button');
            button.className = 'conversation-button';

            if (conversationId === currentConversationId)
                button.classList.add('selected');
            
            button.setAttribute('data-conversation-id', conversationId);
            
            var nameSpan = document.createElement('span');
            nameSpan.innerText = conversationName;
            
            var hoverIcons = document.createElement('div');
            hoverIcons.className = 'hover-icons';
            
            var editIcon = document.createElement('img');

            editIcon.className = 'hover-icon edit-icon';
            editIcon.src = '/static/images/rename.png';
            editIcon.alt = 'Rename';

            editIcon.onclick = (e) => {
                e.stopPropagation();
                editConversationName(conversationId, conversationName);
            };
            
            var deleteIcon = document.createElement('img');

            deleteIcon.className = 'hover-icon delete-icon';
            deleteIcon.src = '/static/images/trash.png';
            deleteIcon.alt = 'Delete';

            deleteIcon.onclick = (e) => {
                e.stopPropagation();
                deleteConversation(conversationId);
            };
            
            hoverIcons.appendChild(editIcon);
            hoverIcons.appendChild(deleteIcon);
            
            button.appendChild(nameSpan);
            button.appendChild(hoverIcons);
            button.onclick = () => selectConversation(conversationId);

            conversationItem.appendChild(button);
            conversationList.appendChild(conversationItem);
        });
    });
}

function editConversationName(conversationId, currentName) {
    const newName = prompt("Enter new conversation name:", currentName);

    if (newName && newName.trim() !== '') {
        fetch(`/edit_conversation_name/${conversationId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                name: newName.trim() 
            })
        })

        .then(response => {
            if (response.ok)
                loadConversationList();
            else
                throw new Error('Failed to rename conversation');
        })

        .catch(error => {
            console.error('Error:', error);
            alert('Failed to rename conversation');
        });
    }
}

function handleDropdownDisplay() {
    const currentModel = document.getElementById('current-model').innerText;
    const links = document.querySelectorAll('.dropdown-content a');

    links.forEach(link => {
        link.classList.toggle('selected', link.innerText === currentModel);
    });
}

function deleteConversation(conversationId) {
    if (confirm("Are you sure you want to delete this conversation?")) {
        fetch(`/delete_conversation/${conversationId}`, {
            method: 'DELETE'
        })

        .then(() => {
            loadConversationList()

            .then(() => {
                getConversations()

                .then(data => {
                    let conversationIds = Object.keys(data);

                    if (conversationIds.length > 0)
                        selectConversation(conversationIds[0]);
                    else
                        createConversation();
                });
            });
        });
    }
}

function loadModels() {
    fetch('/get_models')

    .then(response => response.json())
    .then(data => {
        const modelDropdown = document.getElementById('model-dropdown');
        const currentModel = document.getElementById('current-model');

        currentModel.innerText = "Select a model";

        data.models.forEach(model => {
            if (model.in_use) {
                const modelOption = document.createElement('a');

                modelOption.href = "javascript:void(0)";
                modelOption.innerText = model.name;
                modelOption.onclick = () => selectModel(model.name);
                
                modelDropdown.appendChild(modelOption);
            }
        });
    });
}

function handleFileUpload(event) {
    const files = Array.from(event.target.files);
    const fileDisplay = document.getElementById('file-display');
    const conversationId = currentConversationId;
    
    if (!conversationId)
        return;

    const formData = new FormData();
    formData.append('conversation_id', conversationId);

    files.forEach(file => formData.append('files', file));

    fetch('/upload_files', {
        method: 'POST',
        body: formData
    })

    .then(response => response.json())
    .then(data => {
        const { successFiles, errors, message } = data;

        successFiles.forEach(file => {
            if (!document.querySelector(`.file-name[data-filename="${file.name}"]`)) {
                const fileElement = document.createElement('div');
                fileElement.className = 'file-item';
                
                const randomColor = ['#f47247', '#5856d6', '#3A86FF'][Math.floor(Math.random() * 3)];
                const extension = file.name.split('.').pop().toLowerCase();
                
                const icon = document.createElement('div');

                icon.className = 'file-icon';
                icon.innerText = extension;
                icon.style.backgroundColor = randomColor;
                
                const fileInfo = document.createElement('div');
                fileInfo.className = 'file-info';
                
                const fileName = document.createElement('div');

                fileName.className = 'file-name';
                fileName.setAttribute('data-filename', file.name);
                fileName.innerText = file.name;
                
                const removeButton = document.createElement('button');

                removeButton.className = 'remove-circle';
                removeButton.innerHTML = '×';
                removeButton.onclick = () => {
                    fetch('/remove_file', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            filename: file.name,
                            conversation_id: conversationId
                        })
                    })

                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            fileElement.remove();

                            if (fileDisplay.children.length === 0)
                                fileDisplay.classList.remove('has-files');
                        } else
                            alert('Error removing file: ' + data.message);
                    });
                };
                
                fileInfo.appendChild(fileName);

                fileElement.appendChild(icon);
                fileElement.appendChild(fileInfo);
                fileElement.appendChild(removeButton);

                fileDisplay.appendChild(fileElement);
            }
        });

        if (message)
            alert(message);

        if (fileDisplay.children.length > 0)
            fileDisplay.classList.add('has-files');
    })

    .catch(err => {
        alert(`Unexpected error: ${err}`);
    })

    .finally(() => {
        event.target.value = '';
    });
}

function adjustFooterHeight() {
    const fileDisplay = document.getElementById('file-display');
    const chatFooter = document.querySelector('.chat-footer');
    const fileItems = fileDisplay.querySelectorAll('.file-item').length;

    chatFooter.style.height = fileItems > 0 ? `${50 + fileItems * 35}px` : '50px';
}

function initializeUserIcon() {
    const colors = [
        '#f47247',  // Orange
        '#5856d6',  // Indigo
        '#3A86FF'   // Blue
    ];

    const userColor = colors[Math.floor(Math.random() * colors.length)];
    document.documentElement.style.setProperty('--user-color', userColor);
    
    const userIcon = document.getElementById('user-icon');

    if (userIcon)
        userIcon.innerText = getUserInitials(username);
}

function searchConversations(query) {
    const items = document.querySelectorAll('.conversation-item');
    query = query.toLowerCase();

    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(query) ? 'flex' : 'none';
    });
}

function showContextMenu(conversationId, event) {
    event.preventDefault();
    event.stopPropagation();
    
    const contextMenu = document.getElementById('conversation-context-menu');
    currentContextMenuId = conversationId;
    
    contextMenu.style.top = `${event.pageY}px`;
    contextMenu.style.left = `${event.pageX}px`;
    contextMenu.classList.remove('hidden');
    
    document.addEventListener('click', hideContextMenu);
}

function hideContextMenu() {
    const contextMenu = document.getElementById('conversation-context-menu');
    contextMenu.classList.add('hidden');

    currentContextMenuId = null;
    document.removeEventListener('click', hideContextMenu);
}

function downloadConversation() {
    if (!currentConversationId)
        return;

    fetch('/get_conversations')
        .then(response => response.json())
        .then(data => {
            const conversation = data[currentConversationId];

            if (conversation) {
                const blob = new Blob([JSON.stringify(conversation, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);

                const a = document.createElement('a');

                a.href = url;
                a.download = `conversation_${currentConversationId}.json`;

                document.body.appendChild(a);
                a.click();

                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } else
                alert('Conversation not found');
        })
        .catch(error => alert('Error downloading conversation: ', error));
}

document.addEventListener('DOMContentLoaded', (event) => {
    fetch('/get_username')
        .then(response => response.json())
        .then(data => {
            username = data.username;
            initializeUserIcon();
        });

    loadConversationList()

    .then(() => {
        getConversations()
        .then(data => {
            let conversationIds = Object.keys(data);


            if (conversationIds.length === 0)
                createConversation();
            else if (urlConversationId && urlConversationId !== 'chat' && conversationIds.includes(urlConversationId))
                selectConversation(urlConversationId);
            else
                selectConversation(conversationIds[0]);
        });
    });

    loadModels();
    toggleSendButton();
    handleDropdownDisplay();
    
    initializeUserIcon();
    
    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('input', (e) => searchConversations(e.target.value));
    
    document.querySelector('.dropdown').addEventListener('mouseenter', handleDropdownDisplay);
    
    document.getElementById('send-button').addEventListener('click', sendMessage);
    document.getElementById('message-input').addEventListener('keypress', handleKeyPress);

    document.getElementById('send-button').addEventListener('click', () => {
        if (isResponding) 
            cancelAnimation();
        else
            sendMessage();
    });
    
    const messageInput = document.getElementById('message-input');
    const messageBox = document.querySelector('.message-box');

    const maxHeight = 124;

    messageInput.value = '';
    messageBox.classList.remove('has-content');

    messageInput.style.height = '24px';
    messageBox.style.height = '32px';

    messageInput.addEventListener('input', event => {
        const effectiveLines = getWrapCountUsingCanvas(messageInput);

        const lineHeight = 24;
        const calculatedHeight = effectiveLines * lineHeight;

        if (calculatedHeight <= maxHeight) {
            messageInput.style.height = calculatedHeight + 'px';
            messageInput.style.overflowY = 'hidden';

            messageBox.style.height = (calculatedHeight + 8) + 'px';
        } else {
            messageInput.style.height = maxHeight + 'px';
            messageInput.style.overflowY = 'auto';
            
            messageBox.style.height = (maxHeight + 8) + 'px';
        }
    });
}); 

var _buffer;

function getWrapCountUsingCanvas(textarea) {
    if (_buffer == null) {
        _buffer = document.createElement('textarea');
        
        _buffer.style.border = 'none';
        _buffer.style.height = '0';
        _buffer.style.overflow = 'hidden';
        _buffer.style.padding = '0';
        _buffer.style.position = 'absolute';
        _buffer.style.left = '0';
        _buffer.style.top = '0';
        _buffer.style.zIndex = '-1';

        document.body.appendChild(_buffer);
    }

    var cs = window.getComputedStyle(textarea);
    var pl = parseInt(cs.paddingLeft);
    var pr = parseInt(cs.paddingRight);
    var lh = parseInt(cs.lineHeight);

    if (isNaN(lh))
        lh = parseInt(cs.fontSize);

    _buffer.style.width = (textarea.clientWidth - pl - pr) + 'px';
    _buffer.style.font = cs.font;
    _buffer.style.letterSpacing = cs.letterSpacing;
    _buffer.style.whiteSpace = cs.whiteSpace;
    _buffer.style.wordBreak = cs.wordBreak;
    _buffer.style.wordSpacing = cs.wordSpacing;
    _buffer.style.wordWrap = cs.wordWrap;

    _buffer.value = textarea.value;

    var result = Math.floor(_buffer.scrollHeight / lh);

    if (result == 0)
        result = 1;

    return result;
}
