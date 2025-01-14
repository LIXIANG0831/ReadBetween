'use client';

import { useRouter } from 'next/navigation';
import React, { useEffect } from 'react';
import { encodePassphrase } from '@/lib/client-utils';
import styles from '../styles/Home.module.css';


export default function Page() {
  const router = useRouter();
  useEffect(() => {
    router.push('/form');
    // const serverUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL;
    // const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoibXkgbmFtZSIsInZpZGVvIjp7InJvb21Kb2luIjp0cnVlLCJyb29tIjoibXktcm9vbSIsImNhblB1Ymxpc2giOnRydWUsImNhblN1YnNjcmliZSI6dHJ1ZSwiY2FuUHVibGlzaERhdGEiOnRydWV9LCJzdWIiOiJpZGVudGl0eSIsImlzcyI6ImRldmtleSIsIm5iZiI6MTczNDE5Mjc5NSwiZXhwIjoxNzM0MjE0Mzk1fQ.2VlpBsQYAAaMHJVLUxEMv68TOKalw6ZC8hqofv4vA8s"
    // router.push(`/custom/?liveKitUrl=${serverUrl}&token=${token}#${encodePassphrase("7&UIJHd78i7y")}`,);
  }, []);

  return (
    <>
      <main className={styles.main} data-lk-theme="default">
      </main>
    </>
  );
}
