import express from 'express';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import OpenAI from 'openai';
import { marked } from 'marked';
import { parseArgs } from "node:util";

const app = express();
const port = 3000;

const {values} = parseArgs({options: 
                            {"compile-commands-dir": {type: 'string'}}});

// 현재 모듈의 URL을 파일 경로로 변환
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let compileCommandsJSON;

if ('compile-commands-dir' in values) {
    compileCommandsJSON = path.join(values['compile-commands-dir'], 
                                           'compile_commands.json');
} else {
    compileCommandsJSON = path.join(__dirname, 'compile_commands.json');
}

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

let fileList = [];

fs.readFile(compileCommandsJSON, 'utf8', (err, data) => {
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

// /filelist 경로로 요청이 들어오면 Code Review할 파일 목록을 HTML 형식으로 응답으로 보내기
app.get('/filelist', (req, res) => {
    res.send(`
        <h1>File List</h1>
        <ul>
            ${fileList.map(file => `<li><a href="/review?path=${encodeURIComponent(file)}">${file}</a></li>`).join('')}
        </ul>
    `);
});

// 정적 파일 제공
app.use(express.static(path.join(__dirname, 'public')));

// /files 경로로 요청이 들어오면 파일 목록을 JSON 형식으로 응답으로 보내기 
app.get('/files', (req, res) => {
    res.json(fileList);
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

        res.set('Content-Type', 'text/plain');
        res.send(data);
    });
});

// /review 경로로 요청이 들어오면 파일 내용과 코드 리뷰를 응답으로 보내기
app.get('/review', async (req, res) => {
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
            <a href="/filelist">Back to file list</a>
        `);
    });
});

app.listen(port, () => {
    console.log(`Server is running at http://localhost:${port}`);
});
