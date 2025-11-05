# Google Meet Add-on Configuration

## Setup Instructions

1. Register your add-on in Google Cloud Console:
   - Go to https://console.cloud.google.com
   - Create a new project
   - Note down your Project ID (e.g., my-project-123456)
   - Enable Google Meet API
   - Configure OAuth consent screen
   - Create OAuth 2.0 credentials (Web Application type)
   - Note down your Client ID and Client Secret

2. Update manifest.json for Development:
   - Use your Project ID temporarily in place of APP_ID during development
   - Update webhook URLs with your development server (e.g., ngrok URL)
   - Verify all permissions match your application needs

3. (Later) Publish to Google Workspace Marketplace:
   - This step is only needed when you're ready to deploy
   - Go to https://developers.google.com/workspace/marketplace/
   - Create a new app listing
   - After submission and approval, you'll receive an App ID
   - Update manifest.json with the received App ID

3. Deploy Configuration:
   - Use a secure HTTPS endpoint for webhooks
   - Configure SSL certificates
   - Set up proper CORS headers
   - Enable required Google Cloud APIs:
     * Google Meet API
     * People API
     * Cloud Speech-to-Text (optional)
     * Cloud Text-to-Speech (optional)

4. Environment Variables:
   ```
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   MEET_APP_ID=your_app_id
   WEBHOOK_URL=https://your-domain.com/webhook
   ```

5. Testing:
   - Use Google Meet Add-on testing tools
   - Verify webhook endpoints
   - Test all commands
   - Check notification delivery
   - Validate authentication flow

## Security Considerations

1. Data Protection:
   - All communication must be over HTTPS
   - Store credentials securely
   - Implement proper session management
   - Regular security audits

2. User Privacy:
   - Clear consent mechanisms
   - Data retention policies
   - Compliance with Google Meet policies
   - GDPR/CCPA compliance where applicable

3. Rate Limiting:
   - Implement API request throttling
   - Monitor usage patterns
   - Set up alerts for unusual activity

## Development Notes

1. Local Testing:
   - Use ngrok for webhook testing
   - Mock Meet API responses
   - Test different meeting scenarios
   - Validate error handling

2. Deployment:
   - Use containerization (Docker)
   - Set up monitoring
   - Configure logging
   - Implement health checks

3. Maintenance:
   - Regular dependency updates
   - API version compatibility checks
   - Performance monitoring
   - Error tracking