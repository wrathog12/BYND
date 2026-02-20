import { useState, useEffect } from 'react';

interface LoadingOverlayProps {
    isVisible: boolean;
}

const MESSAGES = [
    { emoji: '🔍', text: 'Scanning SerpApi for high-signal news leads...' },
    { emoji: '⚖️', text: 'Applying Lucrative Intelligence filters & removing noise...' },
    { emoji: '🕸️', text: 'Crawling deep-content with Crawl4AI (handling 50+ sources)...' },
    { emoji: '🔄', text: 'Firecrawl fallback active for paywalled sources...' },
    { emoji: '✍️', text: 'Finalizing 30-word summaries & niche categorization...' },
    { emoji: '💾', text: 'Storing intelligence in secure database...' },
];

export default function LoadingOverlay({ isVisible }: LoadingOverlayProps) {
    const [msgIndex, setMsgIndex] = useState(0);

    useEffect(() => {
        if (!isVisible) {
            setMsgIndex(0);
            return;
        }

        const interval = setInterval(() => {
            setMsgIndex((prev) => {
                if (prev < MESSAGES.length - 1) return prev + 1;
                return prev;
            });
        }, 30000); // Rotate every 30s

        return () => clearInterval(interval);
    }, [isVisible]);

    if (!isVisible) return null;

    return (
        <div className="loading-overlay">
            <div className="loading-content">
                {/* CSS Spinner */}
                <div className="loading-spinner" />

                <h2 className="loading-title">Processing Intelligence</h2>

                <p className="loading-message">
                    {MESSAGES[msgIndex].emoji} {MESSAGES[msgIndex].text}
                </p>

                {/* Progress Dots */}
                <div className="loading-progress">
                    {MESSAGES.map((_, i) => (
                        <div
                            key={i}
                            className={`loading-dot ${i < msgIndex ? 'done' : i === msgIndex ? 'active' : ''}`}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}
