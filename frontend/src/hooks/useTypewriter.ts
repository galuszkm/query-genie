import { useState, useEffect, useRef } from 'react';

/**
 * Hook for typewriter effect on text
 * @param text - The full text to display
 * @param isComplete - Whether the text is complete and ready to type
 * @param speed - Typing speed in ms per tick
 * @returns The currently displayed text (progressively typed)
 */
export function useTypewriter(
  text: string,
  isComplete: boolean,
  speed: number = 10
): string {
  const [displayedText, setDisplayedText] = useState('');
  const hasTypedRef = useRef(false);

  useEffect(() => {
    // If already typed this message, show full text
    if (hasTypedRef.current) {
      setDisplayedText(text);
      return;
    }

    // If not complete yet (still streaming thinking), don't type
    if (!isComplete || !text) {
      setDisplayedText('');
      return;
    }

    // Start typing effect
    let currentIndex = 0;
    setDisplayedText('');

    const timer = setInterval(() => {
      if (currentIndex < text.length) {
        // Add multiple characters per tick for faster typing
        const charsToAdd = Math.min(3, text.length - currentIndex);
        setDisplayedText(text.slice(0, currentIndex + charsToAdd));
        currentIndex += charsToAdd;
      } else {
        clearInterval(timer);
        hasTypedRef.current = true;
      }
    }, speed);

    return () => clearInterval(timer);
  }, [text, isComplete, speed]);

  return displayedText;
}
