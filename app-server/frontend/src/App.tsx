import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import './App.css';

interface Message {
  text: string;
  sender: 'user' | 'ai';
}

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(uuidv4());
  const chatWindowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchGreeting = async () => {
      setIsLoading(true);
      try {
        const response = await fetch('/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: "___INIT_GREETING___",
            sessionId: sessionId,
          }),
        });

        if (!response.ok) throw new Error('Server Error');
        if (!response.body) throw new Error('No response body');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let aiResponseText = '';

        setIsLoading(false);
        setMessages([{ text: '', sender: 'ai' }]);

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          aiResponseText += chunk;

          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1].text = aiResponseText;
            return newMessages;
          });
        }
      } catch (error) {
        console.error(error);
        setMessages([{ text: 'Rosy is busy right now. Please try again later! 🍔', sender: 'ai' }]);
        setIsLoading(false);
      }
    };

    fetchGreeting();
  }, [sessionId]);

  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    setMessages(prev => [...prev, { text, sender: 'user' }]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/chat', { // NestJS is serving at /chat based on global prefix
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          sessionId: sessionId,
        }),
      });

      if (!response.ok) throw new Error('Server Error');
      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let aiResponseText = '';

      setIsLoading(false);
      
      // Add a placeholder for AI response that we will update
      setMessages(prev => [...prev, { text: '', sender: 'ai' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        aiResponseText += chunk;

        setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1].text = aiResponseText;
          return newMessages;
        });
      }
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { text: ' [Error connecting to AI]', sender: 'ai' }]);
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') sendMessage();
  };

  return (
    <div className="phone-container">
      <div className="header">🍔 Gemma Burger Concierge</div>
      <div className="chat-window" ref={chatWindowRef}>
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
        {isLoading && (
          <div className="typing-indicator">
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
          </div>
        )}
      </div>
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your order..."
          onKeyPress={handleKeyPress}
          disabled={isLoading}
        />
        <button onClick={sendMessage} disabled={isLoading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
};

export default App;
