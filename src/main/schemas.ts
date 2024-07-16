import { InferOutput, object, optional, safeParse, string } from 'valibot'

export const PluginPackageJSONSchema = object({
	name: string('Plugin name is required'),
	pluginName: string('Readable plugin name is required'),
	main: string('Plugin main frontend script file is required'),
	styles: optional(string()),
	dockerfile: optional(string())
})

export const parsePluginPackageJSON = (
	data: string
): InferOutput<typeof PluginPackageJSONSchema> | string => {
	try {
		const result = JSON.parse(data)

		const parseResult = safeParse(PluginPackageJSONSchema, result)

		if (parseResult.success) {
			return parseResult.output
		}

		return `Unable to parse plugin package.json file: ${parseResult.issues.join(', ')}`
	} catch (error) {
		return 'Could not parse plugin package.json file'
	}
}
