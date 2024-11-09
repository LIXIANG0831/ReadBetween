// /src/main.ts
import { v4 as uuidv4 } from 'uuid';

// 获取DOM元素
const urlInput = document.getElementById('urlInput') as HTMLInputElement;
const submitBtn = document.getElementById('submitBtn') as HTMLButtonElement;
const placeholder = document.getElementById('placeholder') as HTMLElement;

// 监听提交按钮点击事件
submitBtn.addEventListener('click', () => {
    const url = urlInput.value;
    if (!url) {
        alert('请填写URL');
        return;
    }
    console.log(url)

    // 从URL中提取文件名作为标题
    const title = url.substring(url.lastIndexOf('/') + 1);
    console.log(title)

    // 根据URL的扩展名推断文件类型
    const fileType = url.substring(url.lastIndexOf('.') + 1).toLowerCase();
    console.log(fileType)

    // 生成UUID作为key
    const key = uuidv4();
    console.log(key)

    // 初始化文档编辑器
    const docEditor = new DocsAPI.DocEditor("placeholder", {
        editorConfig: {
            mode: "view",
        },
        document: {
            fileType: fileType,
            key: key,
            title: title,
            url: url,
        },
        documentType: "cell",
    });
});