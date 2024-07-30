import { any, array, includes, object, pipe, string, InferOutput, boolean, nullable } from 'valibot'

export const IFrameMessageSchema = object({
	type: string(),
	data: any()
})

export type IFrameMessage = InferOutput<typeof IFrameMessageSchema>

export const RegisterIFrameSchema = object({
	type: string(),
	data: object({
		pluginName: string('Plugin name is required')
	})
})

export type RegisterIFrame = InferOutput<typeof RegisterIFrameSchema>

export const SendDirectoryContentsSchema = object({
	type: pipe(string(), includes('send-directory-contents')),
	data: object({
		directoryPath: nullable(string('Directory path is required')),
		directoryName: nullable(string('Directory name is required')),
		files: array(string()),
		isFolder: array(boolean())
	})
})

export type SendDirectoryContents = InferOutput<typeof SendDirectoryContentsSchema>

export const ReadFileRequestSchema = object({
	type: pipe(string(), includes('read-file')),
	data: object({
		filePath: string('File path is required')
	})
})

export type ReadFileRequest = InferOutput<typeof ReadFileRequestSchema>

export const ReadFileResponseSchema = object({
	type: pipe(string(), includes('read-file-response')),
	data: object({
		filePath: string('File path is required'),
		contents: string()
	})
})

export type ReadFileResponse = InferOutput<typeof ReadFileResponseSchema>

export const SaveFileRequestSchema = object({
	type: pipe(string(), includes('save-file')),
	data: object({
		filePath: string('File path is required'),
		contents: string('File contents are required')
	})
})

export type SaveFileRequest = InferOutput<typeof SaveFileRequestSchema>
