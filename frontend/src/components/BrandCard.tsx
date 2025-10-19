'use client';

import Image from 'next/image';
import { useRouter } from 'next/navigation';

interface BrandCardProps {
  size?: 'small' | 'medium' | 'large';
  clickable?: boolean;
}

export default function BrandCard({ size = 'medium', clickable = true }: BrandCardProps) {
  const router = useRouter();

  const sizeClasses = {
    small: {
      logo: 'w-8 h-8',
      logoSize: 32,
      text: 'text-2xl',
    },
    medium: {
      logo: 'w-12 h-12',
      logoSize: 48,
      text: 'text-3xl',
    },
    large: {
      logo: 'w-14 h-14',
      logoSize: 56,
      text: 'text-4xl',
    },
  };

  const sizes = sizeClasses[size];

  const handleClick = () => {
    if (clickable) {
      router.push('/');
    }
  };

  return (
    <div
      onClick={handleClick}
      className={`flex items-center gap-2 font-bold text-primary ${
        clickable ? 'hover:text-primary-hover transition-colors cursor-pointer' : ''
      } ${sizes.text}`}
    >
      <Image
        src="/pulse-icon.png"
        alt="Pulse Logo"
        width={sizes.logoSize}
        height={sizes.logoSize}
        className={`${sizes.logo} object-contain`}
      />
      <span>Pulse</span>
    </div>
  );
}
