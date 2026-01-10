import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent } from '../ui/card';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}

export const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, color }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
    >
      <Card interactive>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground font-mono">{title}</p>
              <p className={`text-4xl font-bold mt-2 ${color}`}>{value}</p>
            </div>
            <div className={`${color} opacity-20`}>{icon}</div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};
