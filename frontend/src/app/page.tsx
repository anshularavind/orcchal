"use client";

import { useState, FormEvent } from 'react';
import Image from "next/image";

interface ApiResponse {
  success: boolean;
  message?: string;
  download_url?: string;
  filename?: string;
  error?: string;
}

export default function Home() {
  const [inputUrl, setInputUrl] = useState('');
  const [topic, setTopic] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<ApiResponse | null>(null);
  const [error, setError] = useState<string>('');

  // Backend API base URL - adjust this to match your FastAPI server
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!inputUrl.trim() || !topic.trim()) {
      setError('Please provide both URL and topic');
      return;
    }

    setIsLoading(true);
    setError('');
    setResponse(null);

    try {
      // Call your FastAPI endpoint
      const queryParams = new URLSearchParams({
        input_url: inputUrl.trim(),
        topic: topic.trim()
      });

      const apiResponse = await fetch(`${API_BASE_URL}/input_url?${queryParams}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!apiResponse.ok) {
        throw new Error(`HTTP error! status: ${apiResponse.status}`);
      }

      // Check if the response is a file download
      const contentType = apiResponse.headers.get('content-type');

      if (contentType && (contentType.includes('text/html') || 
                          contentType.includes('application/octet-stream') || 
                          contentType.includes('application/pdf') ||
                          contentType.includes('text/plain'))) {
        // Handle file download
        const blob = await apiResponse.blob();
        const filename = getFilenameFromHeaders(apiResponse.headers) || 'download.html';
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        setResponse({
          success: true,
          message: `File "${filename}" downloaded successfully!`,
          filename
        });
      } else {

        const data = await apiResponse.json();
        setResponse(data);
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
      setError(errorMessage);
      console.error('API call failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getFilenameFromHeaders = (headers: Headers): string | null => {
    const disposition = headers.get('content-disposition');
    if (disposition) {
      const filenameMatch = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (filenameMatch && filenameMatch[1]) {
        return filenameMatch[1].replace(/['"]/g, '');
      }
    }
    return null;
  };

  const handleDownloadAgain = async () => {
    if (response?.download_url) {
      try {
        const link = document.createElement('a');
        link.href = response.download_url;
        link.download = response.filename || 'download.txt';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } catch (err) {
        setError('Failed to download file');
      }
    }
  };

  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-8 row-start-2 items-center sm:items-start max-w-2xl w-full">
        <div className="flex flex-col items-center gap-4">
          <Image
            className="dark:invert"
            src="/next.svg"
            alt="Next.js logo"
            width={180}
            height={38}
            priority
          />
          <h1 className="text-2xl font-bold text-center">
            ORCHIDS CHALLENGE SUBMISSION - Anshul Aravind
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
            Submission to the ORCHIDS challenge, entering a URL and a topic to recreate an aesthetically similar webpage to the URL about the topic. 
          </p>
        </div>

        <form onSubmit={handleSubmit} className="w-full space-y-4">
          <div className="space-y-2">
            <label htmlFor="inputUrl" className="block text-sm font-medium">
              Input URL
            </label>
            <input
              id="inputUrl"
              type="url"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              placeholder="https://example.com"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
              required
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="topic" className="block text-sm font-medium">
              Topic
            </label>
            <input
              id="topic"
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter topic for processing"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-md border border-solid border-transparent transition-colors flex items-center justify-center bg-foreground text-background gap-2 hover:bg-[#383838] dark:hover:bg-[#ccc] font-medium text-sm h-12 px-5 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                Processing...
              </>
            ) : (
              'Generate Download for HTML Preview'
            )}
          </button>
        </form>

        {/* Error Display */}
        {error && (
          <div className="w-full p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <div className="flex items-center gap-2">
              <span className="text-red-600 dark:text-red-400 text-sm font-medium">Error:</span>
              <span className="text-red-700 dark:text-red-300 text-sm">{error}</span>
            </div>
          </div>
        )}

        {/* Success Response Display */}
        {response && response.success && (
          <div className="w-full p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <span className="text-green-600 dark:text-green-400 text-sm font-medium">Success!</span>
                <span className="text-green-700 dark:text-green-300 text-sm">
                  {response.message || 'File processed successfully'}
                </span>
              </div>
              {response.filename && (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Downloaded: <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-xs">{response.filename}</code>
                </p>
              )}
              {response.download_url && (
                <button
                  onClick={handleDownloadAgain}
                  className="mt-2 self-start px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                >
                  Download Again
                </button>
              )}
            </div>
          </div>
        )}

        {/* API Response Display (for debugging) */}
        {response && !response.success && (
          <div className="w-full p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
            <div className="flex items-center gap-2">
              <span className="text-yellow-600 dark:text-yellow-400 text-sm font-medium">Response:</span>
              <span className="text-yellow-700 dark:text-yellow-300 text-sm">
                {response.error || JSON.stringify(response)}
              </span>
            </div>
          </div>
        )}

        <div className="flex gap-4 items-center flex-col sm:flex-row">
          <a
            className="rounded-full border border-solid border-black/[.08] dark:border-white/[.145] transition-colors flex items-center justify-center hover:bg-[#f2f2f2] dark:hover:bg-[#1a1a1a] hover:border-transparent font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 w-full sm:w-auto"
            href="https://nextjs.org/docs"
            target="_blank"
            rel="noopener noreferrer"
          >
            Read Next.js docs
          </a>
        </div>
      </main>

      <footer className="row-start-3 flex gap-6 flex-wrap items-center justify-center text-sm">
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="#"
        >
          Built with Next.js & FastAPI
        </a>
      </footer>
    </div>
  );
}