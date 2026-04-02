declare module 'react-dropzone' {
  export interface DropzoneOptions {
    onDrop?: (acceptedFiles: File[]) => void | Promise<void>
    accept?: Record<string, string[]>
    multiple?: boolean
  }

  export interface DropzoneRootProps extends Record<string, unknown> {
    onClick?: React.MouseEventHandler<HTMLElement>
    onDragEnter?: React.DragEventHandler<HTMLElement>
    onDragLeave?: React.DragEventHandler<HTMLElement>
    onDragOver?: React.DragEventHandler<HTMLElement>
    onDrop?: React.DragEventHandler<HTMLElement>
  }

  export interface DropzoneInputProps extends Record<string, unknown> {
    accept?: string
    multiple?: boolean
    type?: 'file'
    onChange?: React.ChangeEventHandler<HTMLInputElement>
  }

  export interface DropzoneState {
    getRootProps: () => DropzoneRootProps
    getInputProps: () => DropzoneInputProps
    isDragActive: boolean
  }

  export function useDropzone(options?: DropzoneOptions): DropzoneState
}
