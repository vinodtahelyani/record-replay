const canvas = document.getElementById('canvas');
const wrapper = document.getElementById('wrapper');
const codeBlock = document.getElementById('code');
const iframe = document.getElementsByTagName('iframe')[0];
const socket = new WebSocket('ws://localhost:5000/ws');

let iframeRect = iframe.getBoundingClientRect();
let canvasRect = canvas.getBoundingClientRect();
let ratio = 1;
let lastScrollTime = 0;
let keysPressed = [];
const ignore = ['Shift', 'Alt', 'Control', 'Meta', 'Dead', 'Tab'];
const codes = [];
const lastPosition = { x: 0, y: 0 };

const goBack = () => {
    send({ type: 'back' });
}
const showCode = (code) => {
    codes.push(code);
    codeBlock.style.display = 'block';
    codeBlock.innerHTML = codes.join('\n');
}
const socketOpen = (event) => {
    console.log('Connected to WebSocket server');
    send({ type: 'resolution' });
}
const socketMessage = (event) => {
    if (event.data) {
        const info = JSON.parse(event.data);
        if (info.type === 'resolution') {
            const resolution = info.resolution.split('x');
            const width = parseInt(resolution[0]);
            const height = parseInt(resolution[1]);

            iframe.style.display = 'block';
            iframeRect = iframe.getBoundingClientRect();
            ratio = height / iframeRect.height;
            iframe.style.width = Math.ceil((width / ratio)) + 'px';
            
            canvas.style.position = 'absolute';
            canvas.style.top = `${iframeRect.top}px`;
            canvas.style.width = Math.ceil((width / ratio)) + 'px';
            canvas.style.height = `${iframeRect.height}px`;

            wrapper.style.position = 'absolute';
            wrapper.style.top = `${iframeRect.top}px`;
            wrapper.style.width = Math.ceil((width / ratio)) + 'px';
            wrapper.style.height = `${iframeRect.height}px`;

            canvasRect = canvas.getBoundingClientRect();
        } else if (info.type === 'code') {
            showCode(info.code);
        }
    }
}
const socketClose = (event) => {
    console.log('Disconnected from WebSocket server');
}
const socketError = (event) => {
    console.error('WebSocket error: ', event);
}
const debounce = (func, wait) => {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            func.apply(this, args);
        }, wait);
    };
}
const debouncedKeydownHandler = debounce(() => {
    if (keysPressed.length > 0) {
        console.log(keysPressed.join(''))
        send({type: 'type', text: keysPressed.join('')});
        keysPressed = [];
    }
}, 1000);
const onKeyDown = (event) => {
    const key = event.key;
    if (ignore.includes(key)) return;
    if (key === 'Enter') {
        send({ type: 'type', text: keysPressed.join('') + '|enter' });
        keysPressed = [];
        return;
    } else if (key === 'Backspace') {
        if (keysPressed.length > 0) {
            keysPressed.pop();
        } else {
            send({ type: 'type', text: 'delete' });
        }
        return;
    }
    keysPressed.push(key);
    debouncedKeydownHandler();
};

const onWheel = (event) => {
    const currentTime = Date.now();
    if (currentTime - lastScrollTime >= 1200) {
        const startX = Math.ceil((event.clientX - canvasRect.left) * ratio);
        const startY = Math.ceil((event.clientY - canvasRect.top) * ratio);
        lastScrollTime = currentTime;
        const data = { type: 'scroll', x: startX, y: startY };
        if (event.deltaY > 0) {
            data.direction = 'down';
        } else if (event.deltaY < 0) {
            data.direction = 'up';
        } else if (event.deltaX > 0) {
            data.direction = 'right';
        } else if (event.deltaX < 0) {
            data.direction = 'left';
        }
        send(data);
    }
    event.preventDefault();
}
const clickElement = (event) => {
    lastPosition.x = event.clientX - canvasRect.left;
    lastPosition.y = event.clientY - canvasRect.top;
    send({ type: 'click', x: Math.ceil(lastPosition.x * ratio), y: Math.ceil(lastPosition.y * ratio) });
}
const contextMenu = (event) => {
    lastPosition.x = event.clientX - canvasRect.left;
    lastPosition.y = event.clientY - canvasRect.top;
    event.preventDefault();
    wrapper.style.display = 'block';
}

socket.addEventListener('open', socketOpen);
socket.addEventListener('close', socketClose);
socket.addEventListener('error', socketError);
socket.addEventListener('message', socketMessage);

canvas.addEventListener('click', clickElement);
canvas.addEventListener('wheel', onWheel);
canvas.addEventListener('contextmenu', contextMenu);

document.addEventListener('keydown', onKeyDown);

const clearField = () => {
    send({ type: 'clear', x: Math.ceil(lastPosition.x * ratio), y: Math.ceil(lastPosition.y * ratio) });
}
const lockScreen = () => {
    send({ type: 'lock' });
}
const unlockScreen = () => {
    send({type: 'unlock'});
}
const hideKeyboard = () => {
    send({type: 'hideKeyboard'});
}
const sendToBackground = () => {
    send({type: 'background'});
}
const openNotification = () => {
    send({type: 'notification'});
}
const handleOptions = (type) => {
    wrapper.style.display = 'none';
    switch (type) {
        case 'clear':
            clearField();
            break;
        case 'lock':
            lockScreen();
            break;
        case 'unlock':
            unlockScreen();
            break;
        case 'hide':
            hideKeyboard();
            break;
        case 'background':
            sendToBackground();
            break;
        case 'notification':
            openNotification();
            break;
    }
}
const send = (data) => {
    const message = JSON.stringify(data);
    socket.send(message);
}