const {
    app,
    Menu,
    BrowserWindow
} = require('electron')
const path = require('path')
const url = require('url')
const net = require('net')
const HOST = '127.0.0.1'
const PORT = 9876
// var py = require('child_process').spawn('python', ['core.py']),
//     dataString = ''
// if (py != null) {
//     console.log('child process success')
// }
// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let win
let template = [{
    label: '游戏',
    submenu: [{
        label: '开始新游戏'
    }, {
        type: 'separator'
    }, {
        label: '注销账号'
    }, {
        type: 'separator'
    }, {
        label: '退出游戏'
    }]
}, {
    label: '编辑',
    submenu: [{
        label: '刷新'
    }, {
        type: 'separator'
    }, {
        label: '游戏设置'
    }]
}, {
    label: '视图'
}, {
    label: '工具'
}, {
    label: '帮助',
    submenu: [{
        label: '文档'
    }, {
        type: 'separator'
    }, {
        label: '教程'
    }, {
        type: 'separator'
    }, {
        label: '检查更新'
    }, {
        type: 'separator'
    }, {
        label: '关于'
    }]
}]
startServer()

function startServer() {
    var server = net.createServer();
    server.listen(PORT, HOST);
    console.log('Server listening');
    server.on('connection', function(sock) {
        console.log('CONNECTED: ' + sock.remoteAddress + ':' + sock.remotePort);
        // sock.write('get GIH');
        sock.write('get GIH');
        sock.on('data', function(data) {
            console.log(data.toString('utf8'));
        });
        sock.on('close', function(data) {
            console.log('CLOSED: ' + sock.remoteAddress + ':' + sock.remotePort);
        });
    });
}

function createWindow() {
    const menu = Menu.buildFromTemplate(template)
    Menu.setApplicationMenu(menu)
    win = new BrowserWindow({
        width: 800,
        height: 600,
        resizable: false
    })
    win.loadURL(url.format({
        pathname: path.join(__dirname, 'index.html'),
        protocol: 'file:',
        slashes: true
    }))
    win.webContents.openDevTools()
    win.on('closed', () => {
        win = null
    })
}
app.on('ready', createWindow)
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})
