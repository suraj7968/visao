const express = require('express');
const multer = require('multer');
const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');
const path = require('path');

const app = express();
const upload = multer({
  dest: 'uploads/',
  fileFilter: (req, file, cb) => {
    if (!file.mimetype.startsWith('image/')) {
      return cb(new Error('Only image files are allowed!'), false);
    }
    cb(null, true);
  }
});

app.post('/api/process-image', upload.single('image'), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'Image file is required' });

  const tempPath = req.file.path;
  const formData = new FormData();
  formData.append('image', fs.createReadStream(tempPath));

  try {
    const response = await axios.post('http://localhost:5000/process', formData, {
      headers: formData.getHeaders(),
      timeout: 10000,
    });
    res.json(response.data);
  } catch (error) {
    console.error('Error communicating with Python server:', error.message);
    res.status(500).json({ error: 'Failed to process image' });
  } finally {
    fs.unlink(tempPath, (err) => {
      if (err) console.warn('Failed to delete temp file:', err.message);
    });
  }
});

app.listen(3000, () => console.log('Node server running on port 3000'));
