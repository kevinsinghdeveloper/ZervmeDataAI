import { useEffect } from 'react';

const APP_TITLE = 'Zerve Data AI';

export const useBrowserTitle = (): void => {
  useEffect(() => {
    document.title = APP_TITLE;

    return () => {
      document.title = APP_TITLE;
    };
  }, []);
};
