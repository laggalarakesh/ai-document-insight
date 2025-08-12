const { useState, useEffect, useCallback } = React;

// Sample data from the provided JSON
const sampleHistoryData = [
  {
    "id": "1",
    "filename": "john_doe_resume.pdf",
    "uploadDate": "2025-08-12T10:30:00Z",
    "size": "245KB",
    "insights": {
      "summary": "Experienced software engineer with 5+ years in full-stack development. Strong background in React, Node.js, and cloud technologies. Previous roles at tech startups and established companies.",
      "keySkills": ["React", "Node.js", "Python", "AWS", "Docker", "MongoDB"],
      "experience": "5+ years",
      "education": "Bachelor's in Computer Science",
      "highlights": ["Led team of 3 developers", "Increased system performance by 40%", "Built scalable microservices architecture"]
    }
  },
  {
    "id": "2", 
    "filename": "sarah_smith_cv.pdf",
    "uploadDate": "2025-08-12T09:15:00Z",
    "size": "198KB",
    "insights": {
      "summary": "Marketing specialist with expertise in digital marketing and content strategy. 3 years of experience in B2B and B2C environments. Strong analytical and creative skills.",
      "keySkills": ["Digital Marketing", "Content Strategy", "SEO", "Google Analytics", "Social Media", "Adobe Creative Suite"],
      "experience": "3 years",
      "education": "Master's in Marketing",
      "highlights": ["Increased conversion rates by 25%", "Managed $50K marketing budget", "Created viral social media campaign"]
    }
  },
  {
    "id": "3",
    "filename": "mike_johnson_resume.pdf", 
    "uploadDate": "2025-08-11T14:45:00Z",
    "size": "312KB",
    "insights": {
      "summary": "Data scientist with strong background in machine learning and statistical analysis. 4 years experience in healthcare and finance sectors. PhD in Statistics.",
      "keySkills": ["Python", "R", "Machine Learning", "TensorFlow", "SQL", "Tableau", "Statistical Analysis"],
      "experience": "4 years",
      "education": "PhD in Statistics", 
      "highlights": ["Published 8 research papers", "Built predictive models with 95% accuracy", "Reduced operational costs by $2M through data optimization"]
    }
  }
];

const fileValidation = {
  allowedTypes: ["application/pdf"],
  maxSizeBytes: 10485760,
  maxSizeMB: 10
};

// Utility function to format date
const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Mock AI analysis function
const mockAnalyzeDocument = async (file) => {
  // Simulate processing time
  await new Promise(resolve => setTimeout(resolve, 3000));
  
  // Mock insights based on file name or random selection
  const mockInsights = [
    {
      summary: "Experienced project manager with strong leadership skills and technical background. Proven track record in agile methodologies and cross-functional team management.",
      keySkills: ["Project Management", "Agile", "Scrum", "Leadership", "Stakeholder Management", "Risk Assessment"],
      experience: "7+ years",
      education: "MBA in Project Management",
      highlights: ["Delivered 15+ projects on time and under budget", "Improved team productivity by 35%", "Certified PMP and Scrum Master"]
    },
    {
      summary: "Creative designer with expertise in UI/UX design and brand development. Strong portfolio in digital design and user experience optimization.",
      keySkills: ["UI/UX Design", "Figma", "Adobe Creative Suite", "Prototyping", "User Research", "Brand Design"],
      experience: "4 years",
      education: "Bachelor's in Graphic Design",
      highlights: ["Redesigned app interface increasing user engagement by 60%", "Won design award for brand identity project", "Led design system implementation"]
    }
  ];
  
  const randomInsight = mockInsights[Math.floor(Math.random() * mockInsights.length)];
  
  return {
    id: Date.now().toString(),
    filename: file.name,
    uploadDate: new Date().toISOString(),
    size: `${Math.round(file.size / 1024)}KB`,
    insights: randomInsight
  };
};

// Document Insights Component
function DocumentInsights({ document }) {
  const { insights, filename, uploadDate, size } = document;

  return (
    <div>
      <div className="document-info">
        <div className="document-name">{filename}</div>
        <div className="document-meta">
          <span>Size: {size}</span>
          <span>Uploaded: {formatDate(uploadDate)}</span>
        </div>
      </div>

      <div className="insights-section">
        <h3>Summary</h3>
        <p className="summary-text">{insights.summary}</p>
      </div>

      <div className="insights-section">
        <h3>Key Information</h3>
        <div className="info-grid">
          <div className="info-item">
            <div className="info-label">Experience</div>
            <div className="info-value">{insights.experience}</div>
          </div>
          <div className="info-item">
            <div className="info-label">Education</div>
            <div className="info-value">{insights.education}</div>
          </div>
        </div>
      </div>

      <div className="insights-section">
        <h3>Key Skills</h3>
        <div className="skills-grid">
          {insights.keySkills.map((skill, index) => (
            <div key={index} className="skill-tag">{skill}</div>
          ))}
        </div>
      </div>

      <div className="insights-section">
        <h3>Key Highlights</h3>
        <ul className="highlights-list">
          {insights.highlights.map((highlight, index) => (
            <li key={index}>{highlight}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

// File Upload Component
function FileUpload({ onFileAnalyzed, isAnalyzing, progress, currentFile, analysisResult, error }) {
  const [dragOver, setDragOver] = useState(false);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  }, []);

  const handleFileSelect = useCallback((e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileUpload(file);
    }
  }, []);

  const handleFileUpload = async (file) => {
    // Validate file type
    if (!fileValidation.allowedTypes.includes(file.type)) {
      return;
    }

    // Validate file size
    if (file.size > fileValidation.maxSizeBytes) {
      return;
    }

    onFileAnalyzed(file);
  };

  return (
    <div className="upload-section">
      <div className={`upload-area ${dragOver ? 'drag-over' : ''}`}
           onDragOver={handleDragOver}
           onDragLeave={handleDragLeave}
           onDrop={handleDrop}
           onClick={() => document.getElementById('file-input').click()}>
        
        <div className="upload-icon">📄</div>
        <h3 className="upload-title">Upload PDF Document</h3>
        <p className="upload-subtitle">Drag and drop your PDF file here, or click to browse</p>
        
        <button className="btn btn--primary">
          Choose File
        </button>
        
        <div className="upload-restrictions">
          <p>PDF files only • Max {fileValidation.maxSizeMB}MB</p>
        </div>

        <input
          type="file"
          id="file-input"
          className="file-input"
          accept=".pdf"
          onChange={handleFileSelect}
        />

        {currentFile && (
          <div className="progress-container">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }}></div>
            </div>
            <div className="progress-text">
              {progress < 100 ? `Uploading ${currentFile.name}... ${progress}%` : 'Processing...'}
            </div>
          </div>
        )}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
      </div>

      <div className="analysis-panel">
        <div className="analysis-header">
          <h3 className="analysis-title">Analysis Results</h3>
        </div>
        <div className="analysis-content">
          {!currentFile && !analysisResult && (
            <div className="empty-state">
              <div className="empty-state-icon">🔍</div>
              <p>Upload a PDF document to get started with AI-powered analysis</p>
            </div>
          )}

          {isAnalyzing && (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <div className="loading-text">
                <p><strong>Analyzing document...</strong></p>
                <p>Our AI is extracting insights and generating summary</p>
              </div>
            </div>
          )}

          {analysisResult && <DocumentInsights document={analysisResult} />}
        </div>
      </div>
    </div>
  );
}

// History Component
function History({ history, onSelectDocument, selectedDocument, onDeleteDocument }) {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredHistory = history.filter(doc =>
    doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div>
      <div className="history-header">
        <h2>Document History</h2>
        <input
          type="text"
          placeholder="Search documents..."
          className="form-control search-input"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {filteredHistory.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <p>{searchTerm ? 'No documents match your search' : 'No documents uploaded yet'}</p>
        </div>
      ) : (
        <div className="history-grid">
          {filteredHistory.map((document) => (
            <div
              key={document.id}
              className={`history-item ${selectedDocument?.id === document.id ? 'selected' : ''}`}
              onClick={() => onSelectDocument(document)}
            >
              <div className="history-item-header">
                <div>
                  <div className="history-filename">{document.filename}</div>
                  <div className="history-meta">
                    {document.size} • {formatDate(document.uploadDate)}
                  </div>
                </div>
                <button
                  className="delete-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteDocument(document.id);
                  }}
                  title="Delete document"
                >
                  ×
                </button>
              </div>
              <div className="history-preview">
                {document.insights.summary}
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedDocument && (
        <div className="analysis-panel" style={{ marginTop: '24px' }}>
          <div className="analysis-header">
            <h3 className="analysis-title">Document Details</h3>
          </div>
          <div className="analysis-content">
            <DocumentInsights document={selectedDocument} />
          </div>
        </div>
      )}
    </div>
  );
}

// Main App Component
function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [history, setHistory] = useState(sampleHistoryData);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [selectedHistoryDocument, setSelectedHistoryDocument] = useState(null);
  const [error, setError] = useState('');

  const handleFileAnalyzed = async (file) => {
    setError('');
    setCurrentFile(file);
    setUploadProgress(0);
    setAnalysisResult(null);

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval);
          return 100;
        }
        return prev + 10;
      });
    }, 200);

    // Wait for upload to complete, then start analysis
    setTimeout(async () => {
      setIsAnalyzing(true);
      
      try {
        const result = await mockAnalyzeDocument(file);
        setAnalysisResult(result);
        setHistory(prev => [result, ...prev]);
      } catch (err) {
        setError('Analysis failed. Please try again.');
      } finally {
        setIsAnalyzing(false);
      }
    }, 2000);
  };

  const handleSelectHistoryDocument = (document) => {
    setSelectedHistoryDocument(document);
  };

  const handleDeleteDocument = (id) => {
    setHistory(prev => prev.filter(doc => doc.id !== id));
    if (selectedHistoryDocument?.id === id) {
      setSelectedHistoryDocument(null);
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'history') {
      setCurrentFile(null);
      setAnalysisResult(null);
      setUploadProgress(0);
      setIsAnalyzing(false);
      setError('');
    } else {
      setSelectedHistoryDocument(null);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="app-icon">AI</div>
          <div>
            <h1 className="app-title">AI Document Insights</h1>
            <p className="app-subtitle">Professional document analysis powered by artificial intelligence</p>
          </div>
        </div>
      </header>

      <main className="main-container">
        <nav className="tab-navigation">
          <button
            className={`tab-button ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => handleTabChange('upload')}
          >
            📤 Upload & Analyze
          </button>
          <button
            className={`tab-button ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => handleTabChange('history')}
          >
            📚 History ({history.length})
          </button>
        </nav>

        {activeTab === 'upload' && (
          <FileUpload
            onFileAnalyzed={handleFileAnalyzed}
            isAnalyzing={isAnalyzing}
            progress={uploadProgress}
            currentFile={currentFile}
            analysisResult={analysisResult}
            error={error}
          />
        )}

        {activeTab === 'history' && (
          <History
            history={history}
            onSelectDocument={handleSelectHistoryDocument}
            selectedDocument={selectedHistoryDocument}
            onDeleteDocument={handleDeleteDocument}
          />
        )}
      </main>
    </div>
  );
}

// Render the app
ReactDOM.render(<App />, document.getElementById('root'));