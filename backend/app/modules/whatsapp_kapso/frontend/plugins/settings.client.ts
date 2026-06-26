/**
 * Registers the Kapso WhatsApp connect page under Settings → Integrations.
 * Same boundary as the other modules: `~~` reaches the host shell only.
 */
import { registerSettingsPage } from '~~/app/composables/useSettingsRegistry'

export default defineNuxtPlugin(() => {
  registerSettingsPage({
    path: 'whatsapp-kapso',
    category: 'integrations',
    labelKey: 'whatsapp_kapso.settings.title',
    descriptionKey: 'whatsapp_kapso.settings.description',
    icon: 'i-lucide-message-circle',
    permission: 'whatsapp_kapso.settings.write',
    component: () => import('../components/KapsoSettingsPage.vue'),
    searchKeywords: ['whatsapp', 'kapso', 'mensajes', 'messages', 'integracion', 'integration'],
    order: 50
  })
})
