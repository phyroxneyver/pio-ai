import { ReactNode } from "react";

type PageContainerProps = {
  children: ReactNode;
  className?: string;
};

export function PageContainer({ children, className = "" }: PageContainerProps) {
  return (
    <div className={`w-full max-w-full overflow-x-hidden ${className}`}>
      {children}
    </div>
  );
}