/**
 * Emissions API service — no logic yet, stubs only.
 */
export const emissionsApi = {
  list: (_orgId: number, _params?: { skip?: number; limit?: number }) => {
    // TODO: GET /emissions?organization_id=...
    throw new Error('Not implemented')
  },

  getById: (_id: number) => {
    // TODO: GET /emissions/:id
    throw new Error('Not implemented')
  },

  create: (_payload: unknown) => {
    // TODO: POST /emissions
    throw new Error('Not implemented')
  },

  update: (_id: number, _payload: unknown) => {
    // TODO: PATCH /emissions/:id
    throw new Error('Not implemented')
  },

  remove: (_id: number) => {
    // TODO: DELETE /emissions/:id
    throw new Error('Not implemented')
  },
}

export default emissionsApi
