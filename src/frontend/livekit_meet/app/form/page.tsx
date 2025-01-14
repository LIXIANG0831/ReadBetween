'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { encodePassphrase } from '@/lib/client-utils';
import '../../styles/Form.modeule.css';


export default function FormPage() {
  const [formData, setFormData] = useState({ agent_name: '', prompt: '', welcome_words: '' });
  const router = useRouter();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const serverBaseUrl = process.env.NEXT_PUBLIC_BASE_URL;
      const createAgentUrl = `${serverBaseUrl}/api/v1/voice/create_agent`;

      const response = await fetch(createAgentUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_name: formData.agent_name,
          prompt: formData.prompt,
          welcome_words: formData.welcome_words,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const token = data.data.voice_agent_token;
      // console.log(token)
      const serverUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL;
      router.push(
        `/chat/?liveKitUrl=${serverUrl}&token=${token}#${encodePassphrase("7&UIJHd78i7y")}`,
      );
    } catch (error) {
      console.error('Failed to create agent:', error);
    }
  };

  return (
    <div className="form-container">
      <form onSubmit={handleSubmit} className="form">
        <label>
          Agent Name:
          <input type="text" name="agent_name" value={formData.agent_name} onChange={handleChange} />
        </label>
        <label>
          Prompt:
          <input type="text" name="prompt" value={formData.prompt} onChange={handleChange} />
        </label>
        <label>
          Welcome Words:
          <input type="text" name="welcome_words" value={formData.welcome_words} onChange={handleChange} />
        </label>
        <button type="submit">提交</button>
      </form>
    </div>
  );
}