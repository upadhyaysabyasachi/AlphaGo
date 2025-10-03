# Landing Page Planning Assistant

A friendly, interactive tool that guides beginners through planning and designing their perfect landing page or personal portfolio. This tool asks thoughtful questions and generates a comprehensive masterplan.md file as a blueprint for building their site.

## 🚀 Features

- **Conversational Q&A Flow**: Interactive chat interface that asks one question at a time
- **Smart Follow-ups**: Each question builds on previous answers for personalized guidance
- **Visual Options**: Clickable options for sections and visual styles
- **Progress Tracking**: Visual progress bar shows completion status
- **Masterplan Generation**: Creates a detailed markdown blueprint
- **Download Functionality**: Users can download their personalized masterplan.md
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Modern UI**: Beautiful gradient design with smooth animations

## 🎯 How It Works

1. **Welcome & Introduction**: Friendly greeting explaining the process
2. **Guided Questions**: 7 carefully crafted questions covering:
   - Site purpose and goals
   - Target audience
   - Core message
   - Required sections
   - Visual style preferences
   - Content availability
   - Timeline expectations
3. **Interactive Options**: Clickable buttons for common choices
4. **Masterplan Creation**: Generates comprehensive blueprint
5. **Download Ready**: Users get their personalized masterplan.md file

## 📁 File Structure

```
/
├── index.html          # Main application file
└── README.md          # This documentation
```

## 🛠️ Deployment Options

### Option 1: GitHub Pages (Recommended)

1. **Create a GitHub Repository**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Landing Page Planning Assistant"
   git branch -M main
   git remote add origin https://github.com/yourusername/landing-page-planner.git
   git push -u origin main
   ```

2. **Enable GitHub Pages**:
   - Go to your repository settings
   - Scroll to "Pages" section
   - Select "Deploy from a branch"
   - Choose "main" branch and "/ (root)" folder
   - Click "Save"

3. **Access Your Site**:
   - Your site will be available at: `https://yourusername.github.io/landing-page-planner`

### Option 2: Netlify (Drag & Drop)

1. **Build the site** (already done - just the HTML file)
2. **Go to [Netlify](https://netlify.com)**
3. **Drag and drop** the `index.html` file to the deploy area
4. **Get instant URL** for your live site

### Option 3: Vercel

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Deploy**:
   ```bash
   vercel --prod
   ```

### Option 4: Any Web Host

Simply upload the `index.html` file to any web hosting service:
- **Shared Hosting**: Upload via FTP/cPanel
- **CDN Services**: Upload to services like jsDelivr, unpkg
- **Static Site Hosts**: Surge.sh, Firebase Hosting, etc.

## 🎨 Customization

### Colors
The design uses CSS custom properties. To change colors, modify these values in the `<style>` section:

```css
/* Primary gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Accent gradient */
background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
```

### Questions
To modify the questions, edit the `questions` array in the JavaScript:

```javascript
this.questions = [
    {
        question: "Your custom question?",
        key: "customKey",
        followUp: "Follow-up message"
    }
    // ... more questions
];
```

### Styling
The CSS is embedded in the HTML file for easy deployment. All styles are contained within the `<style>` tag and can be customized as needed.

## 📱 Browser Support

- ✅ Chrome (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## 🔧 Technical Details

- **Pure HTML/CSS/JavaScript**: No frameworks or dependencies
- **Responsive Design**: Mobile-first approach
- **Accessibility**: Proper ARIA labels and keyboard navigation
- **Performance**: Lightweight (~50KB total)
- **Offline Capable**: Works without internet connection

## 🎯 Use Cases

Perfect for:
- **Freelancers** planning their portfolio sites
- **Small Businesses** creating landing pages
- **Students** building personal websites
- **Entrepreneurs** planning product launches
- **Anyone** who wants a structured approach to web design

## 📈 Future Enhancements

Potential features to add:
- Multiple question sets for different industries
- Integration with popular website builders
- Template suggestions based on answers
- Export to different formats (PDF, Word)
- Multi-language support
- Advanced customization options

## 🤝 Contributing

This is a standalone tool, but suggestions and improvements are welcome! The code is well-commented and easy to modify.

## 📄 License

This project is open source and available under the MIT License.

---

**Ready to deploy?** Choose your preferred deployment method above and get your Landing Page Planning Assistant live in minutes! 🚀
