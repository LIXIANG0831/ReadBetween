'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { encodePassphrase } from '@/lib/client-utils';
import '../../styles/Form.modeule.css';


export default function FormPage() {
const [formData, setFormData] = useState({ name: '', room: '' }); // 添加状态
const router = useRouter();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value }); // 更新 handleChange 以处理 room
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // 从环境变量中读取基础 URL
      const serverBaseUrl = process.env.NEXT_PUBLIC_BASE_URL;
      // 构建完整的 URL
      const tokenUrl = `${serverBaseUrl}/getToken?name=${encodeURIComponent(formData.name)}&room=${encodeURIComponent(formData.room)}`;
      const response = await fetch(tokenUrl, {
        method: 'GET',
      });
      // 确保响应的状态码是200，表示成功
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      // 解析JSON格式的响应体
      const data = await response.json();
      // 从解析后的对象中提取token
      const token = data.token;
      const serverUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL;
      router.push(
        `/chat/?liveKitUrl=${serverUrl}&token=${token}#${encodePassphrase("7&UIJHd78i7y")}`,
      );
    } catch (error) {
      console.error('Failed to fetch token:', error);
    }
  };

  return (
    <div className="form-container">
      <form onSubmit={handleSubmit} className="form">
        <label>
          Name:
          <input type="text" name="name" value={formData.name} onChange={handleChange} />
        </label>
        <label>
          Room:
          <input type="text" name="room" value={formData.room} onChange={handleChange} />
        </label>
        <button type="submit">提交</button>
      </form>
    </div>
  );
}