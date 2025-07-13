import React, { useState, useEffect, useCallback } from "react";
import "./App.css";
import axios from "axios";
import { useDropzone } from "react-dropzone";
import { 
  Upload, 
  Download, 
  Trash2, 
  File, 
  Image, 
  FileText, 
  FileArchive,
  Video,
  Music,
  Folder,
  Cloud,
  RefreshCw,
  Eye,
  X,
  Calendar,
  HardDrive,
  Plus
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

console.log('Frontend Environment:', {
  BACKEND_URL,
  API,
  NODE_ENV: process.env.NODE_ENV
});

const FileUploader = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const onDrop = useCallback(async (acceptedFiles) => {
    console.log('onDrop triggered with files:', acceptedFiles);
    const file = acceptedFiles[0];
    if (!file) {
      console.log('No file selected');
      return;
    }

    console.log('File selected:', {
      name: file.name,
      size: file.size,
      type: file.type
    });

    console.log('Upload URL:', `${API}/files/upload`);
    console.log('Backend URL:', BACKEND_URL);

    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);
    console.log('FormData created with file');

    try {
      console.log('Starting upload request...');
      const response = await axios.post(
        `${API}/files/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            console.log('Upload progress:', progress + '%');
            setUploadProgress(progress);
          },
        }
      );

      console.log('Upload successful:', response.data);
      onUploadSuccess && onUploadSuccess(response.data);
    } catch (error) {
      console.error('Upload failed:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        config: error.config
      });
      alert('Upload failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      console.log('Upload finished');
      setUploading(false);
      setUploadProgress(0);
    }
  }, [onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled: uploading,
    multiple: false
  });

  return (
    <div className="file-uploader">
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'uploading' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="dropzone-content">
          {uploading ? (
            <div className="upload-progress">
              <Cloud className="upload-icon animate-bounce" size={48} />
              <p className="upload-text">Uploading... {uploadProgress}%</p>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          ) : (
          <div className="upload-zone">
            <div className="upload-content">
              <Upload className="upload-icon" size={32} />
              <div className="upload-text-content">
                <h3>Upload Files</h3>
                {isDragActive ? (
                  <p>Drop the file here...</p>
                ) : (
                  <p>Drag & drop a file here, or <span className="browse-link">browse</span></p>
                )}
              </div>
            </div>
          </div>
          )}
        </div>
      </div>
    </div>
  );
};

const FileList = ({ files, onFileDeleted }) => {
  const [loading, setLoading] = useState(false);
  const [viewingFile, setViewingFile] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [fileContent, setFileContent] = useState(null);
  const [contentType, setContentType] = useState(null);

  const getFileIcon = (mimeType) => {
    if (!mimeType) return <File size={20} className="text-gray-500" />;
    
    if (mimeType.startsWith('image/')) return <Image size={20} className="text-purple-500" />;
    if (mimeType.startsWith('video/')) return <Video size={20} className="text-red-500" />;
    if (mimeType.startsWith('audio/')) return <Music size={20} className="text-green-500" />;
    if (mimeType.includes('pdf') || mimeType.includes('text')) return <FileText size={20} className="text-blue-500" />;
    if (mimeType.includes('zip') || mimeType.includes('rar')) return <FileArchive size={20} className="text-yellow-500" />;
    
    return <File size={20} className="text-gray-500" />;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const viewFile = async (file) => {
    setLoading(true);
    setViewingFile(file);
    setFileContent(null);
    setContentType(null);
    setIsModalOpen(true);

    try {
      // Download file content for viewing
      const response = await axios.get(
        `${API}/files/download/${file.appwrite_file_id}`,
        { responseType: 'blob' }
      );

      const blob = response.data;
      const mimeType = file.mime_type;
      
      if (mimeType.startsWith('image/')) {
        // For images, create object URL for display
        const imageUrl = URL.createObjectURL(blob);
        setFileContent(imageUrl);
        setContentType('image');
      } else if (mimeType.startsWith('text/') || mimeType.includes('json') || mimeType.includes('xml') || mimeType.includes('csv')) {
        // For text files, read as text
        const text = await blob.text();
        setFileContent(text);
        setContentType('text');
      } else if (mimeType.includes('pdf')) {
        // For PDFs, create object URL for iframe
        const pdfUrl = URL.createObjectURL(blob);
        setFileContent(pdfUrl);
        setContentType('pdf');
      } else if (mimeType.startsWith('video/')) {
        // For videos, create object URL
        const videoUrl = URL.createObjectURL(blob);
        setFileContent(videoUrl);
        setContentType('video');
      } else if (mimeType.startsWith('audio/')) {
        // For audio files, create object URL
        const audioUrl = URL.createObjectURL(blob);
        setFileContent(audioUrl);
        setContentType('audio');
      } else {
        // For other file types, show unsupported message
        setContentType('unsupported');
      }
    } catch (error) {
      console.error('Error loading file content:', error);
      setContentType('error');
    } finally {
      setLoading(false);
    }
  };

  const closeModal = () => {
    setIsModalOpen(false);
    // Clean up object URLs to prevent memory leaks
    if (fileContent && (contentType === 'image' || contentType === 'pdf' || contentType === 'video' || contentType === 'audio')) {
      URL.revokeObjectURL(fileContent);
    }
    setFileContent(null);
    setContentType(null);
    setViewingFile(null);
  };

  const downloadFile = async (fileId, fileName) => {
    setLoading(true);
    try {
      const response = await axios.get(
        `${API}/files/download/${fileId}`,
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed: ' + error.response?.data?.detail || error.message);
    } finally {
      setLoading(false);
    }
  };

  const deleteFile = async (fileId, fileName) => {
    if (!window.confirm(`Are you sure you want to delete "${fileName}"?`)) return;

    setLoading(true);
    try {
      await axios.delete(`${API}/files/delete/${fileId}`);
      onFileDeleted && onFileDeleted(fileId);
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Delete failed: ' + error.response?.data?.detail || error.message);
    } finally {
      setLoading(false);
    }
  };

  const renderFileContent = () => {
    if (loading) {
      return (
        <div className="file-content-loading-direct">
          <RefreshCw className="loading-spinner" size={48} />
          <p>Loading file content...</p>
        </div>
      );
    }

    switch (contentType) {
      case 'image':
        return (
          <img 
            src={fileContent} 
            alt={viewingFile?.original_name}
            className="preview-image-direct"
          />
        );
      
      case 'text':
        return (
          <div className="text-preview-direct">
            <pre className="text-content-direct">{fileContent}</pre>
          </div>
        );
      
      case 'pdf':
        return (
          <iframe 
            src={fileContent}
            className="pdf-iframe-direct"
            title={viewingFile?.original_name}
          />
        );
      
      case 'video':
        return (
          <video 
            src={fileContent}
            controls
            className="preview-video-direct"
          />
        );
      
      case 'audio':
        return (
          <div className="audio-preview-direct">
            <audio 
              src={fileContent}
              controls
              className="preview-audio-direct"
            />
          </div>
        );
      
      case 'unsupported':
        return (
          <div className="unsupported-preview-direct">
            <File size={80} className="unsupported-icon" />
            <h4>Preview Not Available</h4>
            <p>This file type cannot be previewed</p>
          </div>
        );
      
      case 'error':
        return (
          <div className="error-preview-direct">
            <X size={80} className="error-icon" />
            <h4>Error Loading File</h4>
            <p>Unable to load file content</p>
          </div>
        );
      
      default:
        return null;
    }
  };

  if (files.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-content">
          <Folder size={80} className="empty-icon" />
          <h3>No files uploaded yet</h3>
          <p>Start by uploading your first file using the upload area above</p>
          <div className="empty-state-features">
            <div className="feature-item">
              <Upload size={16} />
              <span>Drag & Drop</span>
            </div>
            <div className="feature-item">
              <Cloud size={16} />
              <span>Cloud Storage</span>
            </div>
            <div className="feature-item">
              <Eye size={16} />
              <span>Preview Files</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="file-list">
      <div className="file-list-header">
        <div className="header-left">
          <h2>Your Files</h2>
          <span className="file-count">{files.length} file{files.length !== 1 ? 's' : ''}</span>
        </div>
        <div className="header-right">
          <div className="storage-info">
            <HardDrive size={16} />
            <span>Cloud Storage</span>
          </div>
        </div>
      </div>
      
      {/* Desktop Table View */}
      <div className="file-table desktop-view">
        <div className="file-table-header">
          <div className="file-header-name">Name</div>
          <div className="file-header-size">Size</div>
          <div className="file-header-date">Date</div>
          <div className="file-header-actions">Actions</div>
        </div>
        
        {files.map((file) => (
          <div key={file.id} className="file-row">
            <div className="file-name">
              <div className="file-icon">
                {getFileIcon(file.mime_type)}
              </div>
              <div className="file-name-content">
                <span className="file-name-text">{file.original_name}</span>
                <span className="file-type">{file.mime_type}</span>
              </div>
            </div>
            <div className="file-size">{formatFileSize(file.file_size)}</div>
            <div className="file-date">
              <Calendar size={14} />
              {new Date(file.upload_date).toLocaleDateString()}
            </div>
            <div className="file-actions">
              <button
                onClick={() => viewFile(file)}
                className="action-btn view-btn"
                disabled={loading}
                title="View"
              >
                <Eye size={16} />
              </button>
              <button
                onClick={() => downloadFile(file.appwrite_file_id, file.original_name)}
                className="action-btn download-btn"
                disabled={loading}
                title="Download"
              >
                <Download size={16} />
              </button>
              <button
                onClick={() => deleteFile(file.appwrite_file_id, file.original_name)}
                className="action-btn delete-btn"
                disabled={loading}
                title="Delete"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Mobile Card View */}
      <div className="file-cards mobile-view">
        {files.map((file) => (
          <div key={file.id} className="file-card">
            <div className="file-card-header">
              <div className="file-icon-large">
                {getFileIcon(file.mime_type)}
              </div>
              <div className="file-card-info">
                <h4 className="file-card-name">{file.original_name}</h4>
                <p className="file-card-size">{formatFileSize(file.file_size)}</p>
                <p className="file-card-date">
                  <Calendar size={12} />
                  {new Date(file.upload_date).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="file-card-actions">
              <button
                onClick={() => viewFile(file)}
                className="action-btn-mobile view-btn"
                disabled={loading}
              >
                <Eye size={16} />
                <span>View</span>
              </button>
              <button
                onClick={() => downloadFile(file.appwrite_file_id, file.original_name)}
                className="action-btn-mobile download-btn"
                disabled={loading}
              >
                <Download size={16} />
                <span>Download</span>
              </button>
              <button
                onClick={() => deleteFile(file.appwrite_file_id, file.original_name)}
                className="action-btn-mobile delete-btn"
                disabled={loading}
              >
                <Trash2 size={16} />
                <span>Delete</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* File View Modal - Direct Display on Overlay */}
      {isModalOpen && viewingFile && (
        <div className="modal-overlay" onClick={closeModal}>
          <button 
            className="modal-close-overlay"
            onClick={closeModal}
          >
            <X size={24} />
          </button>
          <div className="file-display-direct" onClick={(e) => e.stopPropagation()}>
            {renderFileContent()}
          </div>
        </div>
      )}
    </div>
  );
};

function App() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchFiles = async () => {
    try {
      const response = await axios.get(`${API}/files/list`);
      setFiles(response.data.files);
    } catch (error) {
      console.error('Error fetching files:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleUploadSuccess = (fileData) => {
    console.log('File uploaded:', fileData);
    fetchFiles(); // Refresh file list
  };

  const handleFileDeleted = (deletedFileId) => {
    setFiles(files.filter(file => file.appwrite_file_id !== deletedFileId));
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <RefreshCw className="loading-icon" size={48} />
        <p>Loading your files...</p>
      </div>
    );
  }

  return (
    <div className="App">
      <div className="app-background"></div>
      <div className="app-content">
        <header className="app-header">
          <div className="header-content">
            <div className="logo-section">
              <Cloud className="logo-icon" size={32} />
              <h1>FileVault</h1>
            </div>
            <p className="header-subtitle">Modern cloud file management</p>
          </div>
        </header>

        <main className="main-content">
          <section className="upload-section">
            <FileUploader onUploadSuccess={handleUploadSuccess} />
          </section>

          <section className="files-section">
            <FileList files={files} onFileDeleted={handleFileDeleted} />
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;