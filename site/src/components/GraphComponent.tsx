'use client';
import dynamic from 'next/dynamic';
import { ComponentProps } from 'react';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

export default function GraphComponent(props: any) {
  return <ForceGraph2D {...props} />;
}
