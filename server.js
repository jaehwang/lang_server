import express from 'express';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import OpenAI from 'openai';
import { marked } from 'marked';

const app = express();
const port = 3000;

let fileList = [];

// 현재 모듈의 URL을 파일 경로로 변환
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const client = new OpenAI ({
    apiKey: process.env['OPENAI_API_KEY'],
});

async function getCodeReview(fileContent) {
    try {
        const completion = await client.chat.completions.create({
            model: "gpt-4o",
            messages: [
                { role: "system", content: "You are a helpful assistant that reviews code." },
                { role: "user", content: `Please review the following code in Korean:\n\n${fileContent}` }
            ]
        });

        return completion.choices[0].message.content;
    } catch (error) {
        console.error('Error calling OpenAI API:', error);
        return 'Error calling OpenAI API';
    }
}

// 서버 시작 시 compile_commands.json 파일 읽기
const compileCommandsPath = path.join(__dirname, 'compile_commands.json');
fs.readFile(compileCommandsPath, 'utf8', (err, data) => {
    if (err) {
        console.error('Error reading compile_commands.json:', err);
        return;
    }

    try {
        const compileCommands = JSON.parse(data);
        fileList = compileCommands.map(command => command.file);
    } catch (err) {
        console.error('Error parsing compile_commands.json:', err);
    }
});

// / 경로로 요청이 들어오면 파일 목록을 응답으로 보내기
app.get('/', (req, res) => {
    res.send(`
        <h1>File List</h1>
        <ul>
            ${fileList.map(file => `<li><a href="/file?path=${encodeURIComponent(file)}">${file}</a></li>`).join('')}
        </ul>
    `);
});

// /file 경로로 요청이 들어오면 파일 내용을 응답으로 보내기
app.get('/file', async (req, res) => {
    const filePath = req.query.path;

    if (!filePath) {
        res.status(400).send('File path is required');
        return;
    }

    fs.readFile(filePath, 'utf8', async (err, data) => {
        if (err) {
            res.status(500).send(`Error reading file: ${err.message}`);
            return;
        }

        const codeReview = await getCodeReview(data);
        const codeReviewHtml = marked(codeReview);

        res.send(`
            <h1>File: ${filePath}</h1>
            <pre>${data}</pre>
            <h2>Code Review:</h2>
            ${codeReviewHtml}
            <a href="/">Back to file list</a>
        `);
    });
});

app.listen(port, () => {
    console.log(`Server is running at http://localhost:${port}`);
});
