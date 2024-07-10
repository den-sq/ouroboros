import { object, string } from 'valibot'

const BackprojectResultSchema = object({
	task_id: string('Task ID is required')
})

export default BackprojectResultSchema
