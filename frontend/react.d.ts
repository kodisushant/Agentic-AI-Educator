// Ambient React & JSX type declarations for the Next.js frontend
// Ensures clean compilation across Antigravity IDE and TypeScript services

declare namespace React {
  export interface CSSProperties {
    [key: string]: string | number | undefined;
  }
  export type ReactNode =
    | ReactElement
    | string
    | number
    | boolean
    | null
    | undefined
    | ReactNode[];

  export interface ReactElement<P = any, T extends string | JSXElementConstructor<any> = string | JSXElementConstructor<any>> {
    type: T;
    props: P;
    key: string | null;
  }

  export type JSXElementConstructor<P> = (props: P) => ReactElement<any, any> | null;

  export type FC<P = {}> = (props: P) => ReactElement<any, any> | null;

  export function useState<T>(
    initialState: T | (() => T)
  ): [T, (action: T | ((prevState: T) => T)) => void];

  export function useEffect(effect: () => void | (() => void), deps?: readonly any[]): void;

  export interface MutableRefObject<T> {
    current: T;
  }

  export function useRef<T>(initialValue: T): MutableRefObject<T>;
  export function useRef<T = undefined>(): MutableRefObject<T | undefined>;

  export function useCallback<T extends (...args: any[]) => any>(callback: T, deps: readonly any[]): T;

  export interface ChangeEvent<T = HTMLElement> {
    target: T;
  }

  export interface MouseEvent<T = HTMLElement> {
    stopPropagation: () => void;
    preventDefault: () => void;
  }
}

declare module "react" {
  export = React;
}

declare module "react/jsx-runtime" {
  export const jsx: any;
  export const jsxs: any;
  export const Fragment: any;
}

declare namespace JSX {
  interface Element extends React.ReactElement<any, any> {}
  interface IntrinsicElements {
    [elemName: string]: {
      children?: React.ReactNode;
      style?: React.CSSProperties;
      className?: string;
      onClick?: (e: any) => void;
      onChange?: (e: any) => void;
      disabled?: boolean;
      checked?: boolean;
      value?: string | number | readonly string[];
      readOnly?: boolean;
      spellCheck?: boolean;
      type?: string;
      name?: string;
      id?: string;
      key?: string | number;
      ref?: any;
      [attr: string]: any;
    };
  }
}
